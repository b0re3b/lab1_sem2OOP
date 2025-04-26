package dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import model.Pilot;

public class PilotDAO implements BaseDAO<Pilot, Long> {

    @Override
    public Optional<Pilot> findById(Long id) throws SQLException {
        String sql = "SELECT * FROM pilots WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                Pilot pilot = extractPilotFromResultSet(rs);
                return Optional.of(pilot);
            }

            return Optional.empty();
        }
    }

    @Override
    public List<Pilot> findAll() throws SQLException {
        String sql = "SELECT * FROM pilots";
        List<Pilot> pilots = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Pilot pilot = extractPilotFromResultSet(rs);
                pilots.add(pilot);
            }
        }

        return pilots;
    }

    @Override
    public Pilot save(Pilot pilot) throws SQLException {
        String sql = "INSERT INTO pilots (name, experience_years, license_type, available) VALUES (?, ?, ?, ?)";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            stmt.setString(1, pilot.getName());
            stmt.setInt(2, pilot.getExperienceYears());
            stmt.setString(3, pilot.getLicenseType());
            stmt.setBoolean(4, pilot.getAvailable());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Creating pilot failed, no rows affected.");
            }

            try (ResultSet generatedKeys = stmt.getGeneratedKeys()) {
                if (generatedKeys.next()) {
                    pilot.setId(generatedKeys.getLong(1));
                } else {
                    throw new SQLException("Creating pilot failed, no ID obtained.");
                }
            }
        }

        return pilot;
    }

    @Override
    public Pilot update(Pilot pilot) throws SQLException {
        String sql = "UPDATE pilots SET name = ?, experience_years = ?, license_type = ?, available = ? WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, pilot.getName());
            stmt.setInt(2, pilot.getExperienceYears());
            stmt.setString(3, pilot.getLicenseType());
            stmt.setBoolean(4, pilot.getAvailable());
            stmt.setLong(5, pilot.getId());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Updating pilot failed, no rows affected.");
            }
        }

        return pilot;
    }

    @Override
    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM pilots WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);

            int affectedRows = stmt.executeUpdate();

            return affectedRows > 0;
        }
    }

    public List<Pilot> findAvailable() throws SQLException {
        String sql = "SELECT * FROM pilots WHERE available = true";
        List<Pilot> pilots = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Pilot pilot = extractPilotFromResultSet(rs);
                pilots.add(pilot);
            }
        }

        return pilots;
    }

    public List<Pilot> findByExperienceYearsGreaterThan(int years) throws SQLException {
        String sql = "SELECT * FROM pilots WHERE experience_years > ?";
        List<Pilot> pilots = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setInt(1, years);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Pilot pilot = extractPilotFromResultSet(rs);
                pilots.add(pilot);
            }
        }

        return pilots;
    }

    public List<Pilot> findByLicenseType(String licenseType) throws SQLException {
        String sql = "SELECT * FROM pilots WHERE license_type = ?";
        List<Pilot> pilots = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, licenseType);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Pilot pilot = extractPilotFromResultSet(rs);
                pilots.add(pilot);
            }
        }

        return pilots;
    }

    private Pilot extractPilotFromResultSet(ResultSet rs) throws SQLException {
        Pilot pilot = new Pilot();
        pilot.setId(rs.getLong("id"));
        pilot.setName(rs.getString("name"));
        pilot.setExperienceYears(rs.getInt("experience_years"));
        pilot.setLicenseType(rs.getString("license_type"));
        pilot.setAvailable(rs.getBoolean("available"));

        return pilot;
    }
}