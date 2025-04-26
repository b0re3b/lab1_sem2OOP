package dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import model.Flight;

public class FlightDAO implements BaseDAO<Flight, Long> {

    @Override
    public Optional<Flight> findById(Long id) throws SQLException {
        String sql = "SELECT * FROM flights WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                Flight flight = extractFlightFromResultSet(rs);
                return Optional.of(flight);
            }

            return Optional.empty();
        }
    }

    @Override
    public List<Flight> findAll() throws SQLException {
        String sql = "SELECT * FROM flights";
        List<Flight> flights = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Flight flight = extractFlightFromResultSet(rs);
                flights.add(flight);
            }
        }

        return flights;
    }

    @Override
    public Flight save(Flight flight) throws SQLException {
        String sql = "INSERT INTO flights (flight_number, departure_airport, arrival_airport, " +
                "departure_time, arrival_time, aircraft_type, status) " +
                "VALUES (?, ?, ?, ?, ?, ?, ?)";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            stmt.setString(1, flight.getFlightNumber());
            stmt.setString(2, flight.getDepartureAirport());
            stmt.setString(3, flight.getArrivalAirport());
            stmt.setTimestamp(4, Timestamp.valueOf(flight.getDepartureTime()));
            stmt.setTimestamp(5, Timestamp.valueOf(flight.getArrivalTime()));
            stmt.setString(6, flight.getAircraftType());
            stmt.setString(7, flight.getStatus());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Creating flight failed, no rows affected.");
            }

            try (ResultSet generatedKeys = stmt.getGeneratedKeys()) {
                if (generatedKeys.next()) {
                    flight.setId(generatedKeys.getLong(1));
                } else {
                    throw new SQLException("Creating flight failed, no ID obtained.");
                }
            }
        }

        return flight;
    }

    @Override
    public Flight update(Flight flight) throws SQLException {
        String sql = "UPDATE flights SET flight_number = ?, departure_airport = ?, arrival_airport = ?, " +
                "departure_time = ?, arrival_time = ?, aircraft_type = ?, status = ? " +
                "WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, flight.getFlightNumber());
            stmt.setString(2, flight.getDepartureAirport());
            stmt.setString(3, flight.getArrivalAirport());
            stmt.setTimestamp(4, Timestamp.valueOf(flight.getDepartureTime()));
            stmt.setTimestamp(5, Timestamp.valueOf(flight.getArrivalTime()));
            stmt.setString(6, flight.getAircraftType());
            stmt.setString(7, flight.getStatus());
            stmt.setLong(8, flight.getId());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Updating flight failed, no rows affected.");
            }
        }

        return flight;
    }

    @Override
    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM flights WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);

            int affectedRows = stmt.executeUpdate();

            return affectedRows > 0;
        }
    }

    public List<Flight> findByStatus(String status) throws SQLException {
        String sql = "SELECT * FROM flights WHERE status = ?";
        List<Flight> flights = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, status);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Flight flight = extractFlightFromResultSet(rs);
                flights.add(flight);
            }
        }

        return flights;
    }

    public List<Flight> findByDepartureAirport(String airport) throws SQLException {
        String sql = "SELECT * FROM flights WHERE departure_airport = ?";
        List<Flight> flights = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, airport);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Flight flight = extractFlightFromResultSet(rs);
                flights.add(flight);
            }
        }

        return flights;
    }

    public List<Flight> findByArrivalAirport(String airport) throws SQLException {
        String sql = "SELECT * FROM flights WHERE arrival_airport = ?";
        List<Flight> flights = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, airport);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Flight flight = extractFlightFromResultSet(rs);
                flights.add(flight);
            }
        }

        return flights;
    }

    private Flight extractFlightFromResultSet(ResultSet rs) throws SQLException {
        Flight flight = new Flight();
        flight.setId(rs.getLong("id"));
        flight.setFlightNumber(rs.getString("flight_number"));
        flight.setDepartureAirport(rs.getString("departure_airport"));
        flight.setArrivalAirport(rs.getString("arrival_airport"));

        Timestamp departureTimestamp = rs.getTimestamp("departure_time");
        flight.setDepartureTime(departureTimestamp != null ? departureTimestamp.toLocalDateTime() : null);

        Timestamp arrivalTimestamp = rs.getTimestamp("arrival_time");
        flight.setArrivalTime(arrivalTimestamp != null ? arrivalTimestamp.toLocalDateTime() : null);

        flight.setAircraftType(rs.getString("aircraft_type"));
        flight.setStatus(rs.getString("status"));

        return flight;
    }
}