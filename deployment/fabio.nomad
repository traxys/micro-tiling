# fabio

job "fabio" {
	datacenters = ["dc1"]

	type = "system"

	update {
		stagger = "5s"
		max_parallel = 1
	}

	group "fabio" {
		task "fabio" {
			driver = "docker"

			config {
				network_mode = "host"
				image = "fabiolb/fabio"
			}

			resources {
				network {
					port "lb" {
						static = 9999
					}

					port "ui" {
						static = 9998
					}
				}
			}
		}
	}
}
