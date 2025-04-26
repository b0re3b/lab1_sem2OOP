package dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CrewAssignmentRequestDTO {
    private Long flightId;
    private Long pilotId;
    private Long navigatorId;
    private Long radioOperatorId;
    private List<Long> stewardIds;
}
