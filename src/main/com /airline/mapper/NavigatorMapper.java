package mapper;
import dto.NavigatorDTO;
import model.Navigator;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

/**
 * Mapper interface for converting between Navigator model and NavigatorDTO objects
 * using MapStruct
 */
@Mapper
public interface NavigatorMapper {

    NavigatorMapper INSTANCE = Mappers.getMapper(NavigatorMapper.class);

    /**
     * Converts a Navigator model to NavigatorDTO
     *
     * @param navigator Navigator model object
     * @return NavigatorDTO object
     */
    NavigatorDTO toDTO(Navigator navigator);

    /**
     * Converts a NavigatorDTO to Navigator model
     *
     * @param navigatorDTO NavigatorDTO object
     * @return Navigator model object
     */
    Navigator toEntity(NavigatorDTO navigatorDTO);

    /**
     * Converts a list of Navigator models to a list of NavigatorDTOs
     *
     * @param navigators List of Navigator model objects
     * @return List of NavigatorDTO objects
     */
    List<NavigatorDTO> toDTOList(List<Navigator> navigators);

    /**
     * Converts a list of NavigatorDTOs to a list of Navigator models
     *
     * @param navigatorDTOs List of NavigatorDTO objects
     * @return List of Navigator model objects
     */
    List<Navigator> toEntityList(List<NavigatorDTO> navigatorDTOs);
}