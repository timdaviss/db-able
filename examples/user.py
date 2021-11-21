"""
:date_created: 2021-11-21
"""

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
