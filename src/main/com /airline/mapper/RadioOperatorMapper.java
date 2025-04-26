package mapper;

import dto.RadioOperatorDTO;
import model.RadioOperator;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

/**
 * Mapper interface for converting between RadioOperator model and RadioOperatorDTO objects
 * using MapStruct
 */
@Mapper
public interface RadioOperatorMapper {

    RadioOperatorMapper INSTANCE = Mappers.getMapper(RadioOperatorMapper.class);

    /**
     * Converts a RadioOperator model to RadioOperatorDTO
     *
     * @param radioOperator RadioOperator model object
     * @return RadioOperatorDTO object
     */
    RadioOperatorDTO toDTO(RadioOperator radioOperator);

    /**
     * Converts a RadioOperatorDTO to RadioOperator model
     *
     * @param radioOperatorDTO RadioOperatorDTO object
     * @return RadioOperator model object
     */
    RadioOperator toEntity(RadioOperatorDTO radioOperatorDTO);

    /**
     * Converts a list of RadioOperator models to a list of RadioOperatorDTOs
     *
     * @param radioOperators List of RadioOperator model objects
     * @return List of RadioOperatorDTO objects
     */
    List<RadioOperatorDTO> toDTOList(List<RadioOperator> radioOperators);

    /**
     * Converts a list of RadioOperatorDTOs to a list of RadioOperator models
     *
     * @param radioOperatorDTOs List of RadioOperatorDTO objects
     * @return List of RadioOperator model objects
     */
    List<RadioOperator> toEntityList(List<RadioOperatorDTO> radioOperatorDTOs);
}