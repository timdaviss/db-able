/**
    Stored procedure to list out B Scrollable implementation.
    :date_created: 2021-11-30
 */

USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`B_list`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`B_list`
(
    IN `_limit` INT,
    IN `_after` INT
)
BEGIN

    SELECT * FROM `testing`.`b` WHERE `id` > IFNULL(`_after`, 0) ORDER BY `id` LIMIT `_limit`;

END;
$$
DELIMITER ;
