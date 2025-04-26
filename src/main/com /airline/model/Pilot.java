package model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Pilot {
    private Long id;
    private String name;
    private Integer experienceYears;
    private String licenseType;
    private Boolean available;
}