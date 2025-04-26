package model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FlightCrew {
    private Long id;
    private Long flightId;
    private Long pilotId;
    private Long navigatorId;
    private Long radioOperatorId;
    private List<Long> stewardIds;  // ID всіх стюардес, призначених на рейс
}