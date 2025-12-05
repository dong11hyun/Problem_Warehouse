.
2025-12-05
오늘의 부딪힌 문제 (.sql)
.sql 파일을 깃을 통해 프로젝트에서 주고 받았다
하지만 데이터가 늘어나고 100MB 가 넘어서자 Git에서 파일 용량 한계에 부딪혔다
<GitHub 단일 파일 제한 100MB>


풀스캔 돌리다가 문제점
Error Code: 2013. Lost connection to MySQL server during query
이 에러는 풀스캔(Full Table Scan) 때문에 쿼리가 너무 오래 걸리거나, 메모리를 많이 쓰거나, 서버가 timeout 나서 MySQL 클라이언트가 연결을 잃어버릴 때 발생하는 대표적인 오류야.

즉, 인덱스 안 타고 → 풀스캔 → 쿼리 오래걸림 → MySQL이 타임아웃 / 메모리 부족 → 연결 끊김 흐름으로 발생하는 문제.
