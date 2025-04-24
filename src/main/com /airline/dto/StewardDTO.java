package dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;


@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StewardDTO {
    private Long id;
    private String name;
    private int experienceYears;
    private List<String> languages;
    private boolean available;
}