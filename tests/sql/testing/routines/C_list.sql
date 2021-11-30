/**
    Stored procedure to list out C Paginated implementation.
    :date_created: 2021-11-30
 */

USE `testing`;
DROP PROCEDURE IF EXISTS `testing`.`C_list`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `testing`.`C_list`
(
    IN `_limit` INT,
    IN `_page` INT
)
BEGIN

    DECLARE `_offset` INT;
    DECLARE `_page_number` INT;
    SET `_page_number` = IFNULL(`_page`, 1);
    SET `_offset` = (`_page_number` - 1) * `_limit`;

    SELECT * FROM `testing`.`c` LIMIT `_limit` OFFSET `_offset`;
    SELECT `_page_number` as `page`, COUNT(*) as `total`, `_limit` as `page_size` FROM `testing`.`c`;

END;
$$
DELIMITER ;