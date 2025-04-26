package dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import model.RadioOperator;

public class RadioOperatorDAO implements BaseDAO<RadioOperator, Long> {

    @Override
    public Optional<RadioOperator> findById(Long id) throws SQLException {
        String sql = "SELECT * FROM radio_operators WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                RadioOperator radioOperator = extractRadioOperatorFromResultSet(rs);
                return Optional.of(radioOperator);
            }

            return Optional.empty();
        }
    }

    @Override
    public List<RadioOperator> findAll() throws SQLException {
        String sql = "SELECT * FROM radio_operators";
        List<RadioOperator> radioOperators = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                RadioOperator radioOperator = extractRadioOperatorFromResultSet(rs);
                radioOperators.add(radioOperator);
            }
        }

        return radioOperators;
    }

    @Override
    public RadioOperator save(RadioOperator radioOperator) throws SQLException {
        String sql = "INSERT INTO radio_operators (name, experience_years, certification, available) VALUES (?, ?, ?, ?)";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            stmt.setString(1, radioOperator.getName());
            stmt.setInt(2, radioOperator.getExperienceYears());
            stmt.setString(3, radioOperator.getCertification());
            stmt.setBoolean(4, radioOperator.getAvailable());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Creating radio operator failed, no rows affected.");
            }

            try (ResultSet generatedKeys = stmt.getGeneratedKeys()) {
                if (generatedKeys.next()) {
                    radioOperator.setId(generatedKeys.getLong(1));
                } else {
                    throw new SQLException("Creating radio operator failed, no ID obtained.");
                }
            }
        }

        return radioOperator;
    }

    @Override
    public RadioOperator update(RadioOperator radioOperator) throws SQLException {
        String sql = "UPDATE radio_operators SET name = ?, experience_years = ?, certification = ?, available = ? WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, radioOperator.getName());
            stmt.setInt(2, radioOperator.getExperienceYears());
            stmt.setString(3, radioOperator.getCertification());
            stmt.setBoolean(4, radioOperator.getAvailable());
            stmt.setLong(5, radioOperator.getId());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Updating radio operator failed, no rows affected.");
            }
        }

        return radioOperator;
    }

    @Override
    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM radio_operators WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);

            int affectedRows = stmt.executeUpdate();

            return affectedRows > 0;
        }
    }

    public List<RadioOperator> findAvailable() throws SQLException {
        String sql = "SELECT * FROM radio_operators WHERE available = true";
        List<RadioOperator> radioOperators = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                RadioOperator radioOperator = extractRadioOperatorFromResultSet(rs);
                radioOperators.add(radioOperator);
            }
        }

        return radioOperators;
    }

    public List<RadioOperator> findByExperienceYearsGreaterThan(int years) throws SQLException {
        String sql = "SELECT * FROM radio_operators WHERE experience_years > ?";
        List<RadioOperator> radioOperators = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setInt(1, years);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                RadioOperator radioOperator = extractRadioOperatorFromResultSet(rs);
                radioOperators.add(radioOperator);
            }
        }

        return radioOperators;
    }

    private RadioOperator extractRadioOperatorFromResultSet(ResultSet rs) throws SQLException {
        RadioOperator radioOperator = new RadioOperator();
        radioOperator.setId(rs.getLong("id"));
        radioOperator.setName(rs.getString("name"));
        radioOperator.setExperienceYears(rs.getInt("experience_years"));
        radioOperator.setCertification(rs.getString("certification"));
        radioOperator.setAvailable(rs.getBoolean("available"));

        return radioOperator;
    }
}