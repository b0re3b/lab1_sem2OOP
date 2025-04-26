package mapper;

import dto.CrewDTO;
import model.FlightCrew;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;

/**
 * Mapper interface for converting betweersn FlightCrew model and CrewDTO objects
 * using MapStruct
 */
@Mapper(uses = {FlightMapper.class, PilotMapper.class, NavigatorMapper.class,
        RadioOperatorMapper.class, StewardMapper.class})
public interface CrewMapper {

    CrewMapper INSTANCE = Mappers.getMapper(CrewMapper.class);

    /**
     * Converts a FlightCrew model to CrewDTO
     *
     * @param flightCrew FlightCrew model object
     * @return CrewDTO object
     */
    CrewDTO toDTO(FlightCrew flightCrew);

    /**
     * Converts a CrewDTO to FlightCrew model
     *
     * @param crewDTO CrewDTO object
     * @return FlightCrew model object
     */
    FlightCrew toEntity(CrewDTO crewDTO);
}