package mapper;

import dto.StewardDTO;
import model.Steward;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

/**
 * Mapper interface for converting between Steward model and StewardDTO objects
 * using MapStruct
 */
@Mapper
public interface StewardMapper {

    StewardMapper INSTANCE = Mappers.getMapper(StewardMapper.class);

    /**
     * Converts a Steward model to StewardDTO
     *
     * @param steward Steward model object
     * @return StewardDTO object
     */
    StewardDTO toDTO(Steward steward);

    /**
     * Converts a StewardDTO to Steward model
     *
     * @param stewardDTO StewardDTO object
     * @return Steward model object
     */
    Steward toEntity(StewardDTO stewardDTO);

    /**
     * Converts a list of Steward models to a list of StewardDTOs
     *
     * @param stewards List of Steward model objects
     * @return List of StewardDTO objects
     */
    List<StewardDTO> toDTOList(List<Steward> stewards);

    /**
     * Converts a list of StewardDTOs to a list of Steward models
     *
     * @param stewardDTOs List of StewardDTO objects
     * @return List of Steward model objects
     */
    List<Steward> toEntityList(List<StewardDTO> stewardDTOs);
}