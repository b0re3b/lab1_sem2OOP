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
public class Steward {
    private Long id;
    private String name;
    private Integer experienceYears;
    private List<String> languages;  // Список мов, якими володіє стюардеса
    private Boolean available;
}