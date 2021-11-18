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

END$$
DELIMITER ;
