# micro-tiling

job "micro-tiling" {
	datacenters = ["dc1"]
	type = "service"

	group "api" {
		task "api" {
			driver = "docker"

			env {
				A_PI_ADDRESS = "http://localhost:9999/a-pi"
			}

			config {
				image = "microtiling/api"
				port_map {
					http = 80
				}
			}

			resources {
				network {
					port "http" {}
				}
			}

			service {
				tags = ["urlprefix-/api strip=/api"]
				port = "http"

				check {
					type = "http"
					port = "http"
					path = "/health"
					interval = "5s"
					timeout = "2s"
				}
			}
		}
	}

	group "a-pi" {
		task "a-pi" {
			driver = "docker"

			env {
				MILLLLLLLL_HOST = "millllllll"
				MILLLLLLLL_PORT = "olala"
			}

			config {
				image = "microtiling/a_pi"
				port_map {
					http = 80
				}
			}

			resources {
				network {
					port "http" {}
				}
			}

			service {
				tags = ["urlprefix-/a-pi strip=/a-pi"]
				port = "http"

				check {
					type = "http"
					port = "http"
					path = "/health"
					interval = "5s"
					timeout = "2s"
				}
			}
		}
	}
}

