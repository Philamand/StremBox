# LibreBox

**An open-source seedbox built with ease of use in mind. It provides a simple user interface for managing your seedbox and an extensible API to easily integrate with other tools.**

The LibreBox interface is currently in French, with English documentation. Multi language support is planned for future releases.

## Table of Contents
- [Features](#features)
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

## Self-Hosting
### Prerequisites
- Docker compose
- A [Hanko](https://hanko.io/) instance up and running, with at least one user

### Steps
1. Clone the repository:
   ```bash
   git clone https://codeberg.org/Philamand/LibreBox.git
   ```

2. Navigate to the project directory:
   ```bash
   cd LibreBox
   ```

3. Create a copy of the example env files and update the values as needed:
   ```bash
   cp .env.example .env
   cp .gluetun.env.example .gluetun.env
   cp .transmission.env.example .transmission.env
   ```

4. Copy the `Caddyfile.example` to `Caddyfile` and update the values as needed:
   ```bash
   cp Caddyfile.example Caddyfile
   ```

5. Run the Docker compose command to start the services:
   ```bash
   docker compose up -d
   ```

6. Create a transmission entry in your database:
   ```bash
   docker compose exec fastapi python cli.py transmission-add
   ```

7. Add your Hanko user to the database (you can find/create the `UserId` in the Hanko dashboard):
   ```bash
   docker compose exec fastapi python cli.py user-add <UserId> 1
   ```

8. Access the LibreBox UI by navigating to `https://<your-domain>` in your browser. Log in using your Hanko account.

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
