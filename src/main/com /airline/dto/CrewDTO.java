package dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CrewDTO {
    private Long id;
    private Long flightId;
    private PilotDTO pilot;
    private NavigatorDTO navigator;
    private RadioOperatorDTO radioOperator;
    private List<StewardDTO> stewards;
}