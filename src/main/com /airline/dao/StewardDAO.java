package dao;

import java.sql.Array;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import model.Steward;
import org.postgresql.util.PGobject;
import com.fasterxml.jackson.databind.ObjectMapper;

public class StewardDAO implements BaseDAO<Steward, Long> {
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public Optional<Steward> findById(Long id) throws SQLException {
        String sql = "SELECT * FROM stewards WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                Steward steward = extractStewardFromResultSet(rs);
                return Optional.of(steward);
            }

            return Optional.empty();
        }
    }

    @Override
    public List<Steward> findAll() throws SQLException {
        String sql = "SELECT * FROM stewards";
        List<Steward> stewards = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Steward steward = extractStewardFromResultSet(rs);
                stewards.add(steward);
            }
        }

        return stewards;
    }

    @Override
    public Steward save(Steward steward) throws SQLException {
        String sql = "INSERT INTO stewards (name, experience_years, languages, available) VALUES (?, ?, ?, ?)";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            stmt.setString(1, steward.getName());
            stmt.setInt(2, steward.getExperienceYears());

            // Handle languages as JSON array
            PGobject jsonObject = new PGobject();
            jsonObject.setType("json");
            jsonObject.setValue(objectMapper.writeValueAsString(steward.getLanguages()));
            stmt.setObject(3, jsonObject);

            stmt.setBoolean(4, steward.getAvailable());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Creating steward failed, no rows affected.");
            }

            try (ResultSet generatedKeys = stmt.getGeneratedKeys()) {
                if (generatedKeys.next()) {
                    steward.setId(generatedKeys.getLong(1));
                } else {
                    throw new SQLException("Creating steward failed, no ID obtained.");
                }
            }
        } catch (Exception e) {
            throw new SQLException("Error saving steward", e);
        }

        return steward;
    }

    @Override
    public Steward update(Steward steward) throws SQLException {
        String sql = "UPDATE stewards SET name = ?, experience_years = ?, languages = ?, available = ? WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, steward.getName());
            stmt.setInt(2, steward.getExperienceYears());

            // Handle languages as JSON array
            PGobject jsonObject = new PGobject();
            jsonObject.setType("json");
            jsonObject.setValue(objectMapper.writeValueAsString(steward.getLanguages()));
            stmt.setObject(3, jsonObject);

            stmt.setBoolean(4, steward.getAvailable());
            stmt.setLong(5, steward.getId());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Updating steward failed, no rows affected.");
            }
        } catch (Exception e) {
            throw new SQLException("Error updating steward", e);
        }

        return steward;
    }

    @Override
    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM stewards WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);

            int affectedRows = stmt.executeUpdate();

            return affectedRows > 0;
        }
    }

    public List<Steward> findAvailable() throws SQLException {
        String sql = "SELECT * FROM stewards WHERE available = true";
        List<Steward> stewards = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Steward steward = extractStewardFromResultSet(rs);
                stewards.add(steward);
            }
        }

        return stewards;
    }

    public List<Steward> findByLanguage(String language) throws SQLException {
        // Using PostgreSQL's JSON containment operator @> to check if languages array contains the given language
        String sql = "SELECT * FROM stewards WHERE languages @> ?::jsonb";
        List<Steward> stewards = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            // Create a JSON array string with the single language
            String jsonLanguage = "[\"" + language + "\"]";
            stmt.setString(1, jsonLanguage);

            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Steward steward = extractStewardFromResultSet(rs);
                stewards.add(steward);
            }
        }

        return stewards;
    }

    public List<Steward> findByExperienceYearsGreaterThan(int years) throws SQLException {
        String sql = "SELECT * FROM stewards WHERE experience_years > ?";
        List<Steward> stewards = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setInt(1, years);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Steward steward = extractStewardFromResultSet(rs);
                stewards.add(steward);
            }
        }

        return stewards;
    }

    // Helper method to extract a Steward from ResultSet
    private Steward extractStewardFromResultSet(ResultSet rs) throws SQLException {
        Steward steward = new Steward();
        steward.setId(rs.getLong("id"));
        steward.setName(rs.getString("name"));
        steward.setExperienceYears(rs.getInt("experience_years"));
        steward.setAvailable(rs.getBoolean("available"));

        // Handle languages as JSON array
        String languagesJson = rs.getString("languages");
        try {
            List<String> languages = Arrays.asList(objectMapper.readValue(languagesJson, String[].class));
            steward.setLanguages(languages);
        } catch (Exception e) {
            throw new SQLException("Error parsing languages JSON", e);
        }

        return steward;
    }

}