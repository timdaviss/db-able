/**
    Table for testing data with B Scrollable.
    :date_created: 2021-11-30
 */

USE `testing`;

CREATE TABLE IF NOT EXISTS `testing`.`b`
(
    `id` INT NOT NULL AUTO_INCREMENT,
    `x`  INT NOT NULL,
    `y`  INT NOT NULL,
    PRIMARY KEY (`id`)
);
