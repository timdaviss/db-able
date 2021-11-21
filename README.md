# db-able
![release](https://img.shields.io/github/package-json/v/timdaviss/db-able?label=release&logo=release&style=flat-square)
![build](https://img.shields.io/github/workflow/status/timdaviss/db-able/test?style=flat-square)
![coverage](https://img.shields.io/codecov/c/github/timdaviss/db-able?style=flat-square)
![dependencies](https://img.shields.io/librariesio/release/pypi/db-able?style=flat-square)

Framework to implement basic CRUD operations with DB for [DataObject](https://github.com/do-py-together/do-py).

## Quick start
Set up your connection string to your database.
```python
from db_able import client


client.CONN_STR = '{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}?{query_args}'
```

Implement the mixins into your DataObject to inject CRUD methods.
```python
from do_py import R
from db_able import Creatable, Deletable, Loadable, Savable


class MyObject(Creatable, Deletable, Loadable, Savable):
    db = '{schema_name}'
    _restrictions = {
        'id': R.INT,
        'key': R.INT
        }
    load_params = ['id']
    create_params = ['key']
    delete_params = ['id']
    save_params = ['id', 'key']


my_obj = MyObject.create(key=555)
my_obj = MyObject.load(id=my_obj.id)
my_obj.key = 777
my_obj.save()
my_obj.delete()
```
Classmethods `create`, `load`, and methods `save` and `delete` are made available
to your DataObject class.

Use provided SQL Generating utils to expedite implementation.
```python
from db_able.utils.sql_generator import print_all_sps
from examples.a import A

print_all_sps(A)
```

## Examples
### "A" Python implementation
```python
from do_py import DataObject, R

from db_able import Creatable, Loadable, Savable, Deletable


class Json(DataObject):
    """ Nested Json object for A. """
    _restrictions = {
        'x': R.INT,
        'y': R.INT
        }


class A(Creatable, Loadable, Savable, Deletable):
    """ Basic DBAble implementation for unit tests. """
    db = 'testing'
    _restrictions = {
        'id': R.INT,
        'string': R.NULL_STR,
        'json': R(Json, type(None)),
        'int': R.NULL_INT,
        'float': R.NULL_FLOAT,
        'datetime': R.NULL_DATETIME
        }
    load_params = ['id']
    create_params = ['string', 'json', 'int', 'float', 'datetime']
    save_params = ['id', 'string', 'json', 'int', 'float', 'datetime']
    delete_params = ['id']
```

### "A" MySQL Table structure
```mysql
CREATE TABLE IF NOT EXISTS `testing`.`a`
(
    `id`       INT         NOT NULL AUTO_INCREMENT,
    `string`   VARCHAR(45) NULL,
    `json`     JSON        NULL,
    `int`      INT(11)     NULL,
    `float`    FLOAT       NULL,
    `datetime` TIMESTAMP   NULL,
    PRIMARY KEY (`id`)
);
```

### "A" MySQL CRUD Stored Procedures
```mysql
USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`A_create`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`A_create`
(
    IN `_string` VARCHAR(45),
    IN `_json` JSON,
    IN `_int` INT,
    IN `_float` FLOAT,
    IN `_datetime` TIMESTAMP
)
BEGIN

    INSERT INTO
        `testing`.`a`
        (
            `string`,
            `json`,
            `int`,
            `float`,
            `datetime`
        )
    VALUES
        (
            `_string`,
            `_json`,
            `_int`,
            `_float`,
            `_datetime`
        );
    CALL `testing`.`A_load`(LAST_INSERT_ID());

END;
$$
DELIMITER ;

USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`A_delete`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`A_delete`
(
    IN `_id` INT
)
BEGIN

    DELETE
    FROM
        `testing`.`a`
    WHERE
        `id` = `_id`;
    SELECT ROW_COUNT() AS `deleted`;

END;
$$
DELIMITER ;

USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`A_load`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`A_load`
(
    IN `_id` INT
)
BEGIN

    SELECT *
    FROM
        `testing`.`a`
    WHERE
        `id` = `_id`;

END;
$$
DELIMITER ;

USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`A_save`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`A_save`
(
    IN `_id` INT,
    IN `_string` VARCHAR(45),
    IN `_json` JSON,
    IN `_int` INT,
    IN `_float` FLOAT,
    IN `_datetime` TIMESTAMP
)
BEGIN

    UPDATE
        `testing`.`a`
    SET
        `string`=`_string`,
        `json`=`_json`,
        `int`=`_int`,
        `float`=`_float`,
        `datetime`=`_datetime`
    WHERE
        `id`=`_id`;
    CALL `testing`.`A_load`(`_id`);

END;
$$
DELIMITER ;
```

## Advanced Use Cases
### User
This implementation requires extension of core functionality
to support salting, hashing, and standard password security practices.
```python
import crypt
import hashlib

from do_py import R

from db_able import Loadable, Creatable, Savable, Deletable


class User(Loadable, Creatable, Savable, Deletable):
    """
    User DataObject with DB CRUD implementation.
    Customized to handle password encryption and security standards.
    """
    db = 'testing'
    _restrictions = {
        'user_id': R.INT,
        'username': R.STR,
        'salt': R.STR,
        'hash': R.STR
        }
    _extra_restrictions = {
        'password': R.STR,
        }
    load_params = ['user_id']
    create_params = ['username', 'salt', 'hash']  # password is required. salt and hash are generated.
    save_params = ['user_id', 'username', 'salt', 'hash']
    delete_params = ['user_id']

    @classmethod
    def generate_salt(cls):
        """
        :rtype: str
        """
        return crypt.mksalt(crypt.METHOD_SHA512)

    @classmethod
    def generate_hash(cls, password, salt):
        """
        :type password: str
        :type salt: str
        :rtype: str
        """
        salted_password = password + salt
        return hashlib.sha512(salted_password.encode()).hexdigest()

    @classmethod
    def create(cls, password=None, **kwargs):
        """
        Overloaded to prevent handling raw password in DB.
        :type password: str
        :keyword username: str
        :rtype: User
        """
        password = cls.kwargs_validator('password', password=password)[0][1]
        salt = cls.generate_salt()
        kwargs.update({
            'salt': salt,
            'hash': cls.generate_hash(password, salt)
            })
        return super(User, cls).create(**kwargs)

    def save(self, password=None):
        """
        Overloaded to support updating password with security.
        :type password: str
        :rtype: bool
        """
        if password:
            password = self.kwargs_validator('password', password=password)[0][1]
            self.salt = self.generate_salt()
            self.hash = self.generate_hash(password, self.salt)
        return super(User, self).save()
```

### User MySQL Table Structure
```mysql
CREATE TABLE IF NOT EXISTS `user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `salt` varchar(255) NOT NULL,
  `hash` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`)
);
```

### User MySQL CRUD Stored Procedures
```mysql
USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`User_load`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`User_load`
(
    IN `_user_id` VARCHAR(255)
)
BEGIN

    SELECT * FROM `testing`.`user` WHERE `user_id` = `_user_id`;

END;
$$
DELIMITER ;


USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`User_create`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`User_create`
(
    IN `_username` VARCHAR(255),
    IN `_salt` VARCHAR(255),
    IN `_hash` VARCHAR(255)
)
BEGIN

    INSERT INTO `testing`.`user` (`username`, `salt`, `hash`) VALUES (`_username`, `_salt`, `_hash`);
    CALL `testing`.`User_load`(LAST_INSERT_ID());

END;
$$
DELIMITER ;


USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`User_save`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`User_save`
(
    IN `_user_id` VARCHAR(255),
    IN `_username` VARCHAR(255),
    IN `_salt` VARCHAR(255),
    IN `_hash` VARCHAR(255)
)
BEGIN

    
    UPDATE `testing`.`user` SET `username`=`_username`, `salt`=`_salt`, `hash`=`_hash` WHERE `user_id` = `_user_id`;
    CALL `testing`.`User_load`(`_user_id`);

END;
$$
DELIMITER ;


USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`User_delete`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`User_delete`
(
    IN `_user_id` VARCHAR(255)
)
BEGIN

    DELETE FROM `testing`.`user` WHERE `user_id` = `_user_id`;
    SELECT ROW_COUNT() AS `deleted`;


END;
$$
DELIMITER ;
```

## Best Practices
* It is recommended to store your SQL files within your code repository for ease of reference. Refer to
`do-able/tests/sql` for an example of code organization.
* Generally, explicitly defining the columns for your %s_load stored procedures is better for forward compatibility as
changes are implemented in the long run.

### Testing & Code Quality
Code coverage reports for master, branches, and PRs 
are posted [here in CodeCov](https://codecov.io/gh/timdaviss/db-able).
