package dto;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NavigatorDTO {
    private Long id;
    private String name;
    private int experienceYears;
    private String certificationLevel;
    private boolean available;
}