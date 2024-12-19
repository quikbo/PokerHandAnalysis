DELIMITER // 

A.
CREATE PROCEDURE ShowRawScores(IN StudentSSN VARCHAR(4))
    BEGIN
        SELECT * FROM Rawscores
        WHERE SSN = StudentSSN;
    END //
CALL ShowRawScores('1006');


CREATE VIEW TotalPoints AS
    SELECT HW1, HW2a, HW2b, Midterm, HW3, FExam 
    FROM Rawscores 
    WHERE SSN = '0001';
CREATE VIEW Weights AS
    SELECT HW1, HW2a, HW2b, Midterm, HW3, FExam
    FROM Rawscores 
    WHERE SSN = '0002';

B.
CREATE VIEW WtdPts AS
    SELECT 
        (1/tp.HW1) * w.HW1 as HW1_factor,
        (1/tp.HW2a) * w.HW2a as HW2a_factor,
        (1/tp.HW2b) * w.HW2b as HW2b_factor,
        (1/tp.Midterm) * w.Midterm as Midterm_factor,
        (1/tp.HW3) * w.HW3 as HW3_factor,
        (1/tp.FExam) * w.FExam as FExam_factor
    FROM TotalPoints tp, Weights w;

DECLARE FirstName VARCHAR(11);
        DECLARE LastName VARCHAR(11);
        SELECT FName, LName INTO FirstName, LastName 
        FROM Rawscores 
        WHERE SSN = StudentSSN;

CREATE PROCEDURE ShowPercentages(IN StudentSSN VARCHAR(4))
    BEGIN
        SELECT 
            SSN,
            LName,
            FName,
            Section,
            (r.HW1/tp.HW1) * 100 as HW1_Pct,
            (r.HW2a/tp.HW2a) * 100 as HW2a_Pct,
            (r.HW2b/tp.HW2b) * 100 as HW2b_Pct,
            (r.Midterm/tp.Midterm) * 100 as Midterm_Pct,
            (r.HW3/tp.HW3) * 100 as HW3_Pct,
            (r.FExam/tp.FExam) * 100 as FExam_Pct
        FROM Rawscores r, TotalPoints tp
        WHERE SSN = StudentSSN;

        SELECT CONCAT('The cumulative course average for ', t.F, ' ', t.L, ' is ', t.CumAvg)
        FROM (
            SELECT r.FName AS F, r.LName AS L,
                (r.HW1 * wp.HW1_factor + 
                    r.HW2a * wp.HW2a_factor +
                    r.HW2b * wp.HW2b_factor +
                    r.Midterm * wp.Midterm_factor +
                    r.HW3 * wp.HW3_factor +
                    r.FExam * wp.FExam_factor) * 100 as CumAvg
            FROM Rawscores r, WtdPts wp
            WHERE r.SSN = StudentSSN
        ) AS t;
    END //
CALL ShowPercentages('1006');


C.
CREATE PROCEDURE AllRawScores(IN pass VARCHAR(50))
    BEGIN
        DECLARE valid INT DEFAULT 0;
        
        SELECT COUNT(*) INTO valid
        FROM Passwords 
        WHERE CurPasswords = pass;
        
        IF valid > 0 THEN
            SELECT SSN, LName, FName, Section, 
                HW1, HW2a, HW2b, Midterm, HW3, FExam
            FROM Rawscores 
            WHERE SSN NOT IN ('0001', '0002') 
            ORDER BY Section, LName, FName;
        ELSE
            SELECT 'Invalid password - Access Denied' AS Error;
        END IF;
    END//
CALL AllRawScores('OpenSesame');
CALL AllRawScores('WrongPassword');


D.
CREATE PROCEDURE AllPercentages(IN pass VARCHAR(50))
    BEGIN
        DECLARE valid INT DEFAULT 0;
        
        SELECT COUNT(*) INTO valid
        FROM Passwords 
        WHERE CurPasswords = pass;
        
        IF valid > 0 THEN
            SELECT 
                SSN,
                LName,
                FName,
                Section,
                (r.HW1/tp.HW1) * 100 as HW1_Pct,
                (r.HW2a/tp.HW2a) * 100 as HW2a_Pct,
                (r.HW2b/tp.HW2b) * 100 as HW2b_Pct,
                (r.Midterm/tp.Midterm) * 100 as Midterm_Pct,
                (r.HW3/tp.HW3) * 100 as HW3_Pct,
                (r.FExam/tp.FExam) * 100 as FExam_Pct,
                (r.HW1 * wp.HW1_factor + 
                r.HW2a * wp.HW2a_factor +
                r.HW2b * wp.HW2b_factor +
                r.Midterm * wp.Midterm_factor +
                r.HW3 * wp.HW3_factor +
                r.FExam * wp.FExam_factor) * 100 as CumAvg
            FROM Rawscores r, TotalPoints tp, WtdPts wp
            WHERE SSN NOT IN ('0001', '0002') 
            ORDER BY Section, CumAvg DESC;
        ELSE
            SELECT 'Invalid password - Access Denied' AS Error;
        END IF;
    END//
CALL AllPercentages('OpenSesame');
CALL AllPercentages('WrongPassword');


E.
CREATE VIEW Percentages AS 
    SELECT 
        Section,
        SSN,
        LName,
        FName,
        (r.HW1/tp.HW1) * 100 as HW1_Pct,
        (r.HW2a/tp.HW2a) * 100 as HW2a_Pct,
        (r.HW2b/tp.HW2b) * 100 as HW2b_Pct,
        (r.Midterm/tp.Midterm) * 100 as Midterm_Pct,
        (r.HW3/tp.HW3) * 100 as HW3_Pct,
        (r.FExam/tp.FExam) * 100 as FExam_Pct,
        (r.HW1 * wp.HW1_factor + 
        r.HW2a * wp.HW2a_factor +
        r.HW2b * wp.HW2b_factor +
        r.Midterm * wp.Midterm_factor +
        r.HW3 * wp.HW3_factor +
        r.FExam * wp.FExam_factor) * 100 as WeightedAvg
    FROM Rawscores r, TotalPoints tp, WtdPts wp
    WHERE r.SSN NOT IN ('0001', '0002');

CREATE PROCEDURE Stats(IN pass VARCHAR(50))
    BEGIN
        DECLARE valid INT DEFAULT 0;
        
        SELECT COUNT(*) INTO valid
        FROM Passwords 
        WHERE CurPasswords = pass;
        
        IF valid > 0 THEN
            SELECT * FROM Percentages
            ORDER BY Section, WeightedAvg DESC;

            SELECT 
                'Mean 315' as Statistic,
                AVG(HW1_Pct) as HW1,
                AVG(HW2a_Pct) as HW2a,
                AVG(HW2b_Pct) as HW2b,
                AVG(Midterm_Pct) as Midterm,
                AVG(HW3_Pct) as HW3,
                AVG(FExam_Pct) as FExam,
                AVG(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 315;

            SELECT 
                'Minimum 315' as Statistic,
                MIN(HW1_Pct) as HW1,
                MIN(HW2a_Pct) as HW2a,
                MIN(HW2b_Pct) as HW2b,
                MIN(Midterm_Pct) as Midterm,
                MIN(HW3_Pct) as HW3,
                MIN(FExam_Pct) as FExam,
                MIN(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 315;

            SELECT 
                'Maximum 315' as Statistic,
                MAX(HW1_Pct) as HW1,
                MAX(HW2a_Pct) as HW2a,
                MAX(HW2b_Pct) as HW2b,
                MAX(Midterm_Pct) as Midterm,
                MAX(HW3_Pct) as HW3,
                MAX(FExam_Pct) as FExam,
                MAX(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 315;

            SELECT 
                'Std. Dev. 315' as Statistic,
                STDDEV(HW1_Pct) as HW1,
                STDDEV(HW2a_Pct) as HW2a,
                STDDEV(HW2b_Pct) as HW2b,
                STDDEV(Midterm_Pct) as Midterm,
                STDDEV(HW3_Pct) as HW3,
                STDDEV(FExam_Pct) as FExam,
                STDDEV(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 315;

            SELECT 
                'Mean 415' as Statistic,
                AVG(HW1_Pct) as HW1,
                AVG(HW2a_Pct) as HW2a,
                AVG(HW2b_Pct) as HW2b,
                AVG(Midterm_Pct) as Midterm,
                AVG(HW3_Pct) as HW3,
                AVG(FExam_Pct) as FExam,
                AVG(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 415;

            SELECT 
                'Minimum 415' as Statistic,
                MIN(HW1_Pct) as HW1,
                MIN(HW2a_Pct) as HW2a,
                MIN(HW2b_Pct) as HW2b,
                MIN(Midterm_Pct) as Midterm,
                MIN(HW3_Pct) as HW3,
                MIN(FExam_Pct) as FExam,
                MIN(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 415;

            SELECT 
                'Maximum 415' as Statistic,
                MAX(HW1_Pct) as HW1,
                MAX(HW2a_Pct) as HW2a,
                MAX(HW2b_Pct) as HW2b,
                MAX(Midterm_Pct) as Midterm,
                MAX(HW3_Pct) as HW3,
                MAX(FExam_Pct) as FExam,
                MAX(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 415;

            SELECT 
                'Std. Dev. 415' as Statistic,
                STDDEV(HW1_Pct) as HW1,
                STDDEV(HW2a_Pct) as HW2a,
                STDDEV(HW2b_Pct) as HW2b,
                STDDEV(Midterm_Pct) as Midterm,
                STDDEV(HW3_Pct) as HW3,
                STDDEV(FExam_Pct) as FExam,
                STDDEV(WeightedAvg) as CumAvg
            FROM Percentages
            WHERE Section = 415;
        ELSE
            SELECT 'Invalid password - Access Denied' AS Error;
        END IF;
    END//
CALL Stats('OpenSesame');
CALL Stats('WrongPassword');



F.
CREATE PROCEDURE ChangeScores(IN pass VARCHAR(50), IN StudentSSN VARCHAR(4), IN assignmentName VARCHAR(10), IN newScore INT)
BEGIN
    DECLARE valid INT DEFAULT 0;

    SELECT SSN, LName, FName, Section, 
        HW1, HW2a, HW2b, Midterm, HW3, FExam
    FROM Rawscores 
    WHERE SSN = StudentSSN;

    SELECT COUNT(*) INTO valid
    FROM Passwords 
    WHERE CurPasswords = pass;
    IF valid > 0 THEN
        CASE assignmentName
            WHEN 'HW1' THEN 
                UPDATE Rawscores SET HW1 = newScore WHERE SSN = StudentSSN;
            WHEN 'HW2a' THEN 
                UPDATE Rawscores SET HW2a = newScore WHERE SSN = StudentSSN;
            WHEN 'HW2b' THEN 
                UPDATE Rawscores SET HW2b = newScore WHERE SSN = StudentSSN;
            WHEN 'Midterm' THEN 
                UPDATE Rawscores SET Midterm = newScore WHERE SSN = StudentSSN;
            WHEN 'HW3' THEN 
                UPDATE Rawscores SET HW3 = newScore WHERE SSN = StudentSSN;
            WHEN 'FExam' THEN 
                UPDATE Rawscores SET FExam = newScore WHERE SSN = StudentSSN;
            ELSE
                SELECT CONCAT('Invalid assignment name: ', assignmentName) AS Error;
        END CASE;
        SELECT SSN, LName, FName, Section, 
               HW1, HW2a, HW2b, Midterm, HW3, FExam
        FROM Rawscores 
        WHERE SSN = StudentSSN;
    ELSE
        SELECT 'Invalid password - Access Denied' AS Error;
    END IF;
END //

CALL ChangeScores('OpenSesame','1006','HW3',80);
CALL ChangeScores('WrongPassword','1006','HW3',80);

G. assuming that I just need to carry out part f through the php/html files