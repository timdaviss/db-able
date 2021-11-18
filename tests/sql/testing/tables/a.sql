USE `testing`;

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