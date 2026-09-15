# StremBox

**An open-source seedbox built with ease of use in mind. It provides a simple user interface for managing your seedbox and an extensible API to easily integrate with other tools.**

The StremBox interface is currently in French, with English documentation. Multi language support is planned for future releases.

## Table of Contents
- [Features](#features)
- [Local Installation](#local-installation)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
- [Self-Hosting](#self-hosting)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features
- **Simple UI**: An user-friendly interface for managing your seedbox.
- **Extensible API**: Easily integrate with other tools like Stremio.
- **Easy to self host**: Deploy your own instance with minimal effort.

## Local Installation
### Prerequisites
- Docker compose
- A [Hanko](https://hanko.io/) instance up and running, with at least one user
- [Astral UV](https://github.com/astral-sh/uv) installed on your machine
- [dbmate](https://github.com/amacneil/dbmate) installed on your machine
- A VPN provider supported by [Gluetun](https://github.com/qdm12/gluetun)

### Steps
1. Clone the repository:
   ```bash
   git https://codeberg.org/Philamand/StremBox.git
   ```

2. Navigate to the project directory:
   ```bash
   cd StremBox
   ```

3. Create a copy of the example env files and update the values as needed:
   ```bash
   cp .uv.env.example .env
   nano .env
   cp .gluetun.env.example .gluetun.env
   nano .gluetun.env
   ```

4. Run the Docker compose command to start the services:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

5. Run the tests:
   ```bash
   uv run pytest
   ```

6. Run the migrations:
   ```bash
   dbmate up
   ```

7. Create a transmission entry in your database:
   ```bash
   uv run cli.py transmission-add
   ```

8. Add your Hanko user to the database (you can find/create the `UserId` in the Hanko dashboard):
   ```bash
   uv run cli.py user-add <UserId> 1
   ```

9. Start the development server:
   ```bash
   uv run fastapi dev
   ```

10. Access the StremBox UI by navigating to `http://localhost:8000` in your browser. Log in using your Hanko account.

## Self-Hosting
### Prerequisites
- Docker compose
- A [Hanko](https://hanko.io/) instance up and running, with at least one user

### Steps
1. Clone the repository:
   ```bash
   git clone https://codeberg.org/Philamand/StremBox.git
   ```

2. Navigate to the project directory:
   ```bash
   cd StremBox
   ```

3. Create a copy of the example env files and update the values as needed:
   ```bash
   cp .env.example .env
   nano .env
   cp .gluetun.env.example .gluetun.env
   nano .gluetun.env
   ```

4. On your first run, you need to generate the SSL certificate for your domain:
  ```bash
   cp nginx.conf.setup.example nginx.conf
   nano nginx.conf
   ```

   Replace your-domain.com on line 3 with your actual domain name.

   Then, edit the docker-compose.yml file to update the domain name and commment out line 31 by adding a `#` at the beginning of the line:
   ```bash
   nano docker-compose.yml
   ```

   Run docker compose to start the services:
   ```bash
   docker compose up -d
   ```

   Wait for the services to start, then run the following command to generate the SSL certificate:
   ```bash
   docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d <your-domain> --email <your-email> --agree-tos --no-eff-email
   ```

   Once the certificate is generated, you can uncomment line 31 in the docker-compose.yml file, delete nginx.conf and stop the services:
   ```bash
   nano docker-compose.yml
   rm nginx.conf
   docker compose down
   ```

5. Copy the `nginx.conf.example` to `nginx.conf` and update the values as needed:
   ```bash
   cp nginx.conf.example nginx.conf
   nano nginx.conf
   ```

6. Run the Docker compose command to start the services:
   ```bash
   docker compose up -d
   ```

7. Create a transmission entry in your database:
   ```bash
   docker compose exec fastapi python cli.py transmission-add
   ```

8. Add your Hanko user to the database (you can find/create the `UserId` in the Hanko dashboard):
   ```bash
   docker compose exec fastapi python cli.py user-add <UserId> 1
   ```

9. Access the StremBox UI by navigating to `https://<your-domain>` in your browser. Log in using your Hanko account.

## Contributing
We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/your-feature).
3. Commit your changes (git commit -am 'Add some feature').
4. Push to the branch (git push origin feature/your-feature).
5. Open a Pull Request.

For major changes, please open an issue first to discuss what you would like to change.

You can use AI to help you with code generation and documentation, but please carefully review and test the generated code before committing. **Do not commit AI generated code without understanding what it does and why it was generated.**

## License
This project is licensed under the AGPL License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
- [Transmission](https://transmissionbt.com/)
- [Gluetun](https://github.com/qdm12/gluetun)
- [FastAPI](https://fastapi.tiangolo.com/)
- [dbmate](https://github.com/amacneil/dbmate)
- [Hanko](https://hanko.io/)
