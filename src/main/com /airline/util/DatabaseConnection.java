package util;


import lombok.extern.log4j.Log4j2;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Properties;
import java.io.IOException;
import java.io.InputStream;


@Log4j2
public class DatabaseConnection {
    private static DatabaseConnection instance;
    private Connection connection;
    private String url;
    private String username;
    private String password;


    private DatabaseConnection() {
        Properties props = new Properties();
        try (InputStream input = getClass().getClassLoader().getResourceAsStream("application.properties")) {
            if (input == null) {
                log.error("Не вдалося знайти файл application.properties");
                throw new IOException("Не вдалося знайти файл application.properties");
            }
            props.load(input);

            String host = props.getProperty("db.host", "localhost");
            String port = props.getProperty("db.port", "5432");
            String dbname = props.getProperty("db.name", "airline_company");

            this.url = "jdbc:postgresql://" + host + ":" + port + "/" + dbname;
            this.username = props.getProperty("db.username", "postgres");
            this.password = props.getProperty("db.password", "postgres");

            // Реєстрація драйвера JDBC
            Class.forName("org.postgresql.Driver");

            log.info("Конфігурація бази даних завантажена успішно");
        } catch (IOException e) {
            log.error("Помилка при завантаженні файлу конфігурації", e);
            throw new RuntimeException("Помилка при завантаженні файлу конфігурації", e);
        } catch (ClassNotFoundException e) {
            log.error("Не знайдено драйвер PostgreSQL JDBC", e);
            throw new RuntimeException("Не знайдено драйвер PostgreSQL JDBC", e);
        }
    }


    public static synchronized DatabaseConnection getInstance() {
        if (instance == null) {
            instance = new DatabaseConnection();
        }
        return instance;
    }


    public Connection getConnection() throws SQLException {
        try {
            if (connection == null || connection.isClosed()) {
                log.info("Створення нового підключення до бази даних");
                connection = DriverManager.getConnection(url, username, password);
            }
        } catch (SQLException e) {
            log.error("Помилка при підключенні до бази даних", e);
            throw e;
        }
        return connection;
    }


    public void closeConnection() {
        if (connection != null) {
            try {
                connection.close();
                log.info("Підключення до бази даних закрито");
            } catch (SQLException e) {
                log.error("Помилка при закритті підключення до бази даних", e);
            }
        }
    }
}