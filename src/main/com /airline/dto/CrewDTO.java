package dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;


@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CrewDTO {
    private Long id;
    private Long flightId;
    private PilotDTO pilot;
    private NavigatorDTO navigator;
    private RadioOperatorDTO radioOperator;
    private List<StewardDTO> stewards;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
