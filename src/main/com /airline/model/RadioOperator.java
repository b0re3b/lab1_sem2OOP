package model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RadioOperator {
    private Long id;
    private String name;
    private Integer experienceYears;
    private String certification;
    private Boolean available;
}