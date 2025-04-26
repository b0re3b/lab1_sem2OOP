package dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class FlightSearchRequestDTO {
    private String departureAirport;
    private String arrivalAirport;
    private LocalDateTime departureTimeFrom;
    private LocalDateTime departureTimeTo;
    private String status;
}