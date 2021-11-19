/**
    Stored procedure to update a testing `A` DataObject
    :date_created: 2021-11-18
 */

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
