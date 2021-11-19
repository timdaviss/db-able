/**
    Stored procedure to delete a testing `A` DataObject
    :date_created: 2021-11-18
 */

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
