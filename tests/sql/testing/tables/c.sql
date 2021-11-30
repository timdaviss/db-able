/**
    Table for testing data with C Paginated.
    :date_created: 2021-11-30
 */

USE `testing`;

CREATE TABLE IF NOT EXISTS `testing`.`c`
(
    `id` INT NOT NULL AUTO_INCREMENT,
    `x`  INT NOT NULL,
    `y`  INT NOT NULL,
    PRIMARY KEY (`id`)
);
