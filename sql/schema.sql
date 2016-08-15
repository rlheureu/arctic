CREATE DATABASE `arctic` /*!40100 DEFAULT CHARACTER SET latin1 */;

CREATE TABLE `arctic_component` (
  `arctic_component_id` int(11) NOT NULL AUTO_INCREMENT,
  `vendor_name` varchar(500) DEFAULT NULL,
  `brand_name` varchar(500) DEFAULT NULL,
  `model_number` varchar(500) DEFAULT NULL,
  `max_performance` varchar(500) DEFAULT NULL,
  `active` int(11) DEFAULT NULL,
  `data_type_discriminator` varchar(45) DEFAULT NULL,
  `generation` varchar(500) DEFAULT NULL,
  `int_gpu` varchar(500) DEFAULT NULL,
  `socket` varchar(500) DEFAULT NULL,
  `ddr3` varchar(500) DEFAULT NULL,
  `ddr3l` varchar(500) DEFAULT NULL,
  `ddr4` varchar(500) DEFAULT NULL,
  `max_memory_size` varchar(500) DEFAULT NULL,
  `unlocked` int(11) DEFAULT NULL,
  `dx12_cap` int(11) DEFAULT NULL,
  `display_port` int(11) DEFAULT NULL,
  `hdmi` int(11) DEFAULT NULL,
  `dvi` int(11) DEFAULT NULL,
  `vga` int(11) DEFAULT NULL,
  `memory_capacity` varchar(500) DEFAULT NULL,
  `memory_config` varchar(500) DEFAULT NULL,
  `memory_spec` varchar(500) DEFAULT NULL,
  `memory_frequency` varchar(500) DEFAULT NULL,
  `color` varchar(500) DEFAULT NULL,
  `chipset_vendor` varchar(500) DEFAULT NULL,
  `chipset_name` varchar(500) DEFAULT NULL,
  `form_factor` varchar(500) DEFAULT NULL,
  `memory_type` varchar(500) DEFAULT NULL,
  `external_ports` varchar(500) DEFAULT NULL,
  `pcie_bus` varchar(500) DEFAULT NULL,
  `mpcie` varchar(500) DEFAULT NULL,
  `size` varchar(500) DEFAULT NULL,
  `resolution` varchar(500) DEFAULT NULL,
  `max_framerate` varchar(500) DEFAULT NULL,
  `recommended` int(11) DEFAULT NULL,
  `sort_order` int(11) DEFAULT '0',
  `display_name` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`arctic_component_id`)
) ENGINE=InnoDB AUTO_INCREMENT=163 DEFAULT CHARSET=latin1;


CREATE TABLE `arctic_user` (
  `arctic_user_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `fb_id` varchar(100) DEFAULT NULL,
  `profile_name` varchar(100) DEFAULT NULL,
  `how_hear` varchar(1000) DEFAULT NULL,
  `fb_token` text,
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `active` int(11) DEFAULT NULL,
  `confirmed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`arctic_user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;


CREATE TABLE `arctic_user_role` (
  `arctic_user_role_id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`arctic_user_role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `arctic_roles_users` (
  `user_id` int(11) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  KEY `roles_users_role_idx` (`role_id`),
  KEY `roles_users_user_idx` (`user_id`),
  CONSTRAINT `roles_users_role` FOREIGN KEY (`role_id`) REFERENCES `arctic_user_role` (`arctic_user_role_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `roles_users_user` FOREIGN KEY (`user_id`) REFERENCES `arctic_user` (`arctic_user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `arctic_rig` (
  `arctic_rig_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(400) DEFAULT NULL,
  `cpu_component_id` int(11) DEFAULT NULL,
  `memory_component_id` int(11) DEFAULT NULL,
  `motherboard_component_id` int(11) DEFAULT NULL,
  `display_component_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `gpu_component_id` int(11) DEFAULT NULL,
  `power_component_id` int(11) DEFAULT NULL,
  `chassis_component_id` int(11) DEFAULT NULL,
  `storage_component_id` int(11) DEFAULT NULL,
  `rig_preset` int(11) DEFAULT '0',
  `rig_preset_name` varchar(400) DEFAULT NULL,
  `rig_preset_sort_order` int(11) DEFAULT '0',
  `rig_preset_description` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`arctic_rig_id`),
  KEY `cpu_component_id_idx` (`cpu_component_id`),
  KEY `user_idx` (`user_id`),
  KEY `display_component_idx` (`display_component_id`),
  KEY `memory_component_idx` (`memory_component_id`),
  KEY `motherboard_compoent_idx` (`motherboard_component_id`),
  KEY `gpu_component_idx` (`gpu_component_id`),
  KEY `storage_component_idx` (`storage_component_id`),
  KEY `chassis_component_idx` (`chassis_component_id`),
  KEY `power_compnent_idx` (`power_component_id`),
  CONSTRAINT `chassis_component` FOREIGN KEY (`chassis_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `cpu_component` FOREIGN KEY (`cpu_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `display_component` FOREIGN KEY (`display_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `gpu_component` FOREIGN KEY (`gpu_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `memory_component` FOREIGN KEY (`memory_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `motherboard_compoent` FOREIGN KEY (`motherboard_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `power_compnent` FOREIGN KEY (`power_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `storage_component` FOREIGN KEY (`storage_component_id`) REFERENCES `arctic_component` (`arctic_component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `user` FOREIGN KEY (`user_id`) REFERENCES `arctic_user` (`arctic_user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=latin1;


CREATE TABLE `arctic_account_claim` (
  `arctic_account_claim_id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(100) DEFAULT NULL,
  `account_claim_type` varchar(45) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `expiration` datetime DEFAULT NULL,
  `claimed` int(11) DEFAULT NULL,
  PRIMARY KEY (`arctic_account_claim_id`),
  KEY `user_idx` (`user_id`),
  CONSTRAINT `acctclaimuser` FOREIGN KEY (`user_id`) REFERENCES `arctic_user` (`arctic_user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

