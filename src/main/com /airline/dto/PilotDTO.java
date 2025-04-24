package dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;


@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PilotDTO {
    private Long id;
    private String name;
    private int experienceYears;
    private String licenseType;
    private boolean available;
}