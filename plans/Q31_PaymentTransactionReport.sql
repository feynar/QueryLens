SELECT
    T.uidTicketID,
    T.lngTicketNumber,
    T.strTicketType,
    DC.uidDeptID,
    DC.dtmZeeDate,
    Z.lngZeeNumber,
    T.dtmPostedTime,
    T.uidEmplID
FROM tblDailyCloses DC
JOIN tblZees Z ON DC.uidDailyCloseID = Z.uidDailyCloseID
JOIN tblTickets T ON Z.uidZeeID = T.uidZeeID
LEFT JOIN tblTicketTrans TT ON T.uidTicketID = TT.uidTicketID
WHERE DC.uidDeptID = '55452bac-40fd-4928-9f45-e85d48352c90'
AND DC.dtmZeeDate >= '2026-02-17'
AND DC.dtmZeeDate < DATEADD(DAY, 1, '2026-04-17')