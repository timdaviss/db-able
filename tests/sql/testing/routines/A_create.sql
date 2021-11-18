/**
    Stored procedure to create a testing `A` DataObject
    :date_created: 2021-11-18
 */

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
