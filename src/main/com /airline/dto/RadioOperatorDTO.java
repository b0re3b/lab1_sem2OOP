package dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RadioOperatorDTO {
    private Long id;
    private String name;
    private int experienceYears;
    private String certification;
    private boolean available;
}