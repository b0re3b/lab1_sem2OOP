package model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {
    private Long id;
    private String username;
    private String password;  // Зберігається в хешованому вигляді
    private String role;  // Можливі ролі: ADMIN, DISPATCHER
    private String email;
    private String fullName;
}