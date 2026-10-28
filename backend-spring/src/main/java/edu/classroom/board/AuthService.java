package edu.classroom.board;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.Date;
import javax.crypto.SecretKey;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class AuthService {
  private final SecretKey key;
  private final String issuer;
  private final String audience;
  private final int ttl;
  private final Users users;

  public AuthService(@Value("${app.jwt.secret}") String secret,
      @Value("${app.jwt.issuer}") String issuer,
      @Value("${app.jwt.audience}") String audience,
      @Value("${app.jwt.ttl}") int ttl, Users users) {
    if (secret == null || !secret.matches("[0-9a-fA-F]{64}"))
      throw new IllegalArgumentException("JWT_SECRET은 새로 생성한 64자리 16진수여야 합니다.");
    if (issuer == null || issuer.isBlank() || audience == null || audience.isBlank() || ttl <= 0)
      throw new IllegalArgumentException("JWT 설정을 확인하세요.");
    this.key = Keys.hmacShaKeyFor(java.util.HexFormat.of().parseHex(secret));
    this.issuer = issuer;
    this.audience = audience;
    this.ttl = ttl;
    this.users = users;
  }

  public String issueToken(Users.PublicUser user) {
    Instant now = Instant.now();
    return Jwts.builder().subject(Long.toString(user.id())).issuer(issuer)
        .audience().add(audience).and().issuedAt(Date.from(now))
        .expiration(Date.from(now.plusSeconds(ttl))).signWith(key, Jwts.SIG.HS256).compact();
  }

  public long currentUserId(HttpServletRequest request) {
    String header = request.getHeader("Authorization");
    if (header == null || !header.matches("Bearer [^\\s]+"))
      throw new ApiError(401, "TOKEN_REQUIRED", "Bearer 토큰이 필요합니다.");
    try {
      var parsed = Jwts.parser().verifyWith(key).build()
          .parseSignedClaims(header.substring(7));
      if (!"HS256".equals(parsed.getHeader().getAlgorithm())) throw new JwtException("algorithm");
      Claims claims = parsed.getPayload();
      if (claims.getExpiration() == null || !issuer.equals(claims.getIssuer())
          || claims.getAudience() == null || claims.getAudience().size() != 1
          || !claims.getAudience().contains(audience)) throw new JwtException("claims");
      String subject = claims.getSubject();
      if (subject == null || !subject.matches("[1-9][0-9]*")) throw new JwtException("subject");
      long id = Long.parseLong(subject);
      if (users.find(id) == null) throw new JwtException("user");
      return id;
    } catch (ExpiredJwtException e) {
      throw new ApiError(401, "TOKEN_EXPIRED", "로그인 시간이 만료되었습니다. 다시 로그인하세요.");
    } catch (JwtException | IllegalArgumentException e) {
      throw new ApiError(401, "INVALID_TOKEN", "유효하지 않은 토큰입니다.");
    }
  }

  public void assertOwner(long userId, long authorId) {
    if (userId != authorId)
      throw new ApiError(403, "FORBIDDEN", "본인이 작성한 글만 변경할 수 있습니다.");
  }
}
