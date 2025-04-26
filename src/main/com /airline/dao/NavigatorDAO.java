package dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import model.Navigator;

public class NavigatorDAO implements BaseDAO<Navigator, Long> {

    @Override
    public Optional<Navigator> findById(Long id) throws SQLException {
        String sql = "SELECT * FROM navigators WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                Navigator navigator = extractNavigatorFromResultSet(rs);
                return Optional.of(navigator);
            }

            return Optional.empty();
        }
    }

    @Override
    public List<Navigator> findAll() throws SQLException {
        String sql = "SELECT * FROM navigators";
        List<Navigator> navigators = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Navigator navigator = extractNavigatorFromResultSet(rs);
                navigators.add(navigator);
            }
        }

        return navigators;
    }

    @Override
    public Navigator save(Navigator navigator) throws SQLException {
        String sql = "INSERT INTO navigators (name, experience_years, certification_level, available) VALUES (?, ?, ?, ?)";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            stmt.setString(1, navigator.getName());
            stmt.setInt(2, navigator.getExperienceYears());
            stmt.setString(3, navigator.getCertificationLevel());
            stmt.setBoolean(4, navigator.getAvailable());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Creating navigator failed, no rows affected.");
            }

            try (ResultSet generatedKeys = stmt.getGeneratedKeys()) {
                if (generatedKeys.next()) {
                    navigator.setId(generatedKeys.getLong(1));
                } else {
                    throw new SQLException("Creating navigator failed, no ID obtained.");
                }
            }
        }

        return navigator;
    }

    @Override
    public Navigator update(Navigator navigator) throws SQLException {
        String sql = "UPDATE navigators SET name = ?, experience_years = ?, certification_level = ?, available = ? WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, navigator.getName());
            stmt.setInt(2, navigator.getExperienceYears());
            stmt.setString(3, navigator.getCertificationLevel());
            stmt.setBoolean(4, navigator.getAvailable());
            stmt.setLong(5, navigator.getId());

            int affectedRows = stmt.executeUpdate();

            if (affectedRows == 0) {
                throw new SQLException("Updating navigator failed, no rows affected.");
            }
        }

        return navigator;
    }

    @Override
    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM navigators WHERE id = ?";

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setLong(1, id);

            int affectedRows = stmt.executeUpdate();

            return affectedRows > 0;
        }
    }

    public List<Navigator> findAvailable() throws SQLException {
        String sql = "SELECT * FROM navigators WHERE available = true";
        List<Navigator> navigators = new ArrayList<>();

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                Navigator navigator = extractNavigatorFromResultSet(rs);
                navigators.add(navigator);
            }
        }

        return navigators;
    }

    public List<Navigator> findByExperienceYearsGreaterThan(int years) throws SQLException {
        String sql = "SELECT * FROM navigators WHERE experience_years > ?";
        List<Navigator> navigators = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setInt(1, years);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Navigator navigator = extractNavigatorFromResultSet(rs);
                navigators.add(navigator);
            }
        }

        return navigators;
    }

    public List<Navigator> findByCertificationLevel(String certificationLevel) throws SQLException {
        String sql = "SELECT * FROM navigators WHERE certification_level = ?";
        List<Navigator> navigators = new ArrayList<>();

        try (Connection conn = getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, certificationLevel);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                Navigator navigator = extractNavigatorFromResultSet(rs);
                navigators.add(navigator);
            }
        }

        return navigators;
    }

    private Navigator extractNavigatorFromResultSet(ResultSet rs) throws SQLException {
        Navigator navigator = new Navigator();
        navigator.setId(rs.getLong("id"));
        navigator.setName(rs.getString("name"));
        navigator.setExperienceYears(rs.getInt("experience_years"));
        navigator.setCertificationLevel(rs.getString("certification_level"));
        navigator.setAvailable(rs.getBoolean("available"));

        return navigator;
    }
}