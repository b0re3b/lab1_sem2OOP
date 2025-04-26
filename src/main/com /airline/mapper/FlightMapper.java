package mapper;
import dto.FlightDTO;
import model.Flight;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

/**
 * Mapper interface for converting between Flight model and FlightDTO objects
 * using MapStruct
 */
@Mapper
public interface FlightMapper {

    FlightMapper INSTANCE = Mappers.getMapper(FlightMapper.class);

    /**
     * Converts a Flight model to FlightDTO
     *
     * @param flight Flight model object
     * @return FlightDTO object
     */
    FlightDTO toDTO(Flight flight);

    /**
     * Converts a FlightDTO to Flight model
     *
     * @param flightDTO FlightDTO object
     * @return Flight model object
     */
    Flight toEntity(FlightDTO flightDTO);

    /**
     * Converts a list of Flight models to a list of FlightDTOs
     *
     * @param flights List of Flight model objects
     * @return List of FlightDTO objects
     */
    List<FlightDTO> toDTOList(List<Flight> flights);

    /**
     * Converts a list of FlightDTOs to a list of Flight models
     *
     * @param flightDTOs List of FlightDTO objects
     * @return List of Flight model objects
     */
    List<Flight> toEntityList(List<FlightDTO> flightDTOs);
}