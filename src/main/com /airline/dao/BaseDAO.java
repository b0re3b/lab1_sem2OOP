package dao;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

import util.DatabaseConnection;

/**
 * Generic DAO interface defining basic CRUD operations
 */
public interface BaseDAO<T, ID> {
    /**
     * Find entity by its ID
     * @param id entity ID
     * @return Optional containing entity if found
     * @throws SQLException if database error occurs
     */
    Optional<T> findById(ID id) throws SQLException;

    /**
     * Find all entities
     * @return List of all entities
     * @throws SQLException if database error occurs
     */
    List<T> findAll() throws SQLException;

    /**
     * Save a new entity
     * @param entity entity to save
     * @return saved entity with generated ID
     * @throws SQLException if database error occurs
     */
    T save(T entity) throws SQLException;

    /**
     * Update an existing entity
     * @param entity entity to update
     * @return updated entity
     * @throws SQLException if database error occurs
     */
    T update(T entity) throws SQLException;

    /**
     * Delete entity by ID
     * @param id entity ID to delete
     * @return true if deleted successfully
     * @throws SQLException if database error occurs
     */
    boolean delete(ID id) throws SQLException;

    /**
     * Get database connection
     * @return active database connection
     * @throws SQLException if connection cannot be established
     */
    default Connection getConnection() throws SQLException {
        return DatabaseConnection.getInstance().getConnection();
    }
}