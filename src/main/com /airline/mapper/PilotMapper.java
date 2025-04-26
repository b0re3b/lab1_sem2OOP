package mapper;

import dto.PilotDTO;
import model.Pilot;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

/**
 * Mapper interface for converting between Pilot model and PilotDTO objects
 * using MapStruct
 */
@Mapper
public interface PilotMapper {

    PilotMapper INSTANCE = Mappers.getMapper(PilotMapper.class);

    /**
     * Converts a Pilot model to PilotDTO
     *
     * @param pilot Pilot model object
     * @return PilotDTO object
     */
    PilotDTO toDTO(Pilot pilot);

    /**
     * Converts a PilotDTO to Pilot model
     *
     * @param pilotDTO PilotDTO object
     * @return Pilot model object
     */
    Pilot toEntity(PilotDTO pilotDTO);

    /**
     * Converts a list of Pilot models to a list of PilotDTOs
     *
     * @param pilots List of Pilot model objects
     * @return List of PilotDTO objects
     */
    List<PilotDTO> toDTOList(List<Pilot> pilots);

    /**
     * Converts a list of PilotDTOs to a list of Pilot models
     *
     * @param pilotDTOs List of PilotDTO objects
     * @return List of Pilot model objects
     */
    List<Pilot> toEntityList(List<PilotDTO> pilotDTOs);
}