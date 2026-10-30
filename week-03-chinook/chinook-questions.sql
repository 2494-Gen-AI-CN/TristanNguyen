-- Chinook query activity (week 3, Thursday). Write one query under each question.
-- How to run this file, what the tables are and what each question expects is in
-- README.md beside it. Test each query at the mysql> prompt first, then paste it here.
-- Hand-in: week-03/hackathon/chinook/chinook-questions.sql in your own learner repo.
-- cp ~/dev/demos/activities/week-03-chinook/chinook-questions.sql ~/dev/TristanNguyen/week-03-chinook/chinook-questions.sql
USE Chinook;


-- ============================================================
-- Part A: one table (SELECT, WHERE, ORDER BY, LIMIT)
-- ============================================================

-- Q01. Every genre name, A to Z.
SELECT name 
FROM Genre
ORDER BY name ASC;

-- Q02. The customers who live in Canada: first name, last name and city, sorted by city.
SELECT FirstName, LastName, City
FROM Customer
WHERE Country = 'Canada'
ORDER BY city;

-- Q03. The ten longest tracks that run over 10 minutes: name and length in minutes
--      (one decimal), longest first.
SELECT Name, Round(Milliseconds/60000.0, 1) AS minutes
FROM Track
WHERE (Milliseconds/60000.0) > 10
ORDER BY Milliseconds DESC 
LIMIT 10;

-- Q04. Invoices from 2025 whose total is above 10: invoice id, date and total, highest total first.
SELECT InvoiceId, InvoiceDate as date, Total
FROM Invoice
WHERE total > 10 AND YEAR(InvoiceDate) = 2025
ORDER BY total DESC;

-- Q05. Albums whose title contains the word Live, A to Z.
SELECT Title
FROM Album
where title LIKE '%Live%'
ORDER BY title;

-- Q06. Customers in the USA or Canada who gave a company name: the full name in one
--      column called customer, the company and the country, sorted by company.
SELECT CONCAT(FirstName, " ", LastName) AS customer, Company, Country
FROM Customer
WHERE Country IN ("USA", "CANADA")
ORDER BY Company;

-- ============================================================
-- Part B: aggregates (GROUP BY, HAVING)
-- ============================================================

-- Q07. One row about the whole Track table: how many tracks, and the shortest, longest
--      and average length in minutes (two decimals).
SELECT COUNT(*) AS tracks, 
        ROUND(MIN(Milliseconds)/60000.0,  2) AS shortest, 
        ROUND(MAX(Milliseconds)/60000.0,  2) AS longest,
        ROUND(AVG(Milliseconds)/60000.0,  2) AS average
FROM Track;

-- Q08. How many customers live in each country, most customers first, then country A to Z.
SELECT COUNT(Country) as customers, Country
FROM Customer
GROUP BY Country
ORDER BY customers DESC, Country ASC;

-- Q09. Total billed per billing country (two decimals), only the countries billed more
--      than 100 in all, highest first.
SELECT ROUND(SUM(Total), 2) AS total_billed, BillingCountry
FROM Invoice
GROUP BY BillingCountry
ORDER BY total_billed DESC;

-- Q10. Albums with more than 25 tracks: the album id and its track count, most tracks first.
--      (Only the id for now. Q13 adds the title.)
SELECT Album.AlbumId, COUNT(TrackId) as track_count  
FROM Album
INNER JOIN Track ON  Album.AlbumID = Track.AlbumId
GROUP BY Album.AlbumId
HAVING track_count > 25
ORDER BY track_count DESC;

-- Q11. Per customer id: how many invoices and how much they spent in all (two decimals),
--      only the customers who spent more than 45, biggest spender first.
SELECT Customer.CustomerId, COUNT(Invoice.InvoiceId) as invoices, SUM(Invoice.Total) as lifetime_spending
FROM Customer
INNER JOIN Invoice on Invoice.CustomerId = Customer.CustomerId
GROUP BY Customer.CustomerId
HAVING lifetime_spending > 45
ORDER BY lifetime_spending DESC;

-- ============================================================
-- Part C: joins
-- ============================================================

-- Q12. Every album title with the name of its artist, sorted by artist then title.
SELECT Album.Title, Artist.Name
FROM Album
INNER JOIN Artist ON Album.ArtistId = Artist.ArtistId
ORDER BY Artist.Name, Album.Title;

-- Q13. Q10 again, with the album title and the artist name instead of the id.
SELECT CONCAT(Album.Title, ", ", Artist.Name) AS album_artist, COUNT(TrackId) as track_count  
FROM Album
INNER JOIN Track ON Album.AlbumID = Track.AlbumId
INNER JOIN Artist ON Artist.ArtistId = Album.ArtistId
GROUP BY Album.AlbumId
HAVING track_count > 25
ORDER BY track_count DESC;

-- Q14. Every track by Iron Maiden: album title and track name, sorted by album then track.
SELECT Album.Title, Track.Name
FROM Track
INNER JOIN Album on Album.AlbumID = Track.AlbumId
INNER JOIN Artist on Album.ArtistId = Artist.ArtistId
WHERE Artist.Name = 'Iron Maiden'
ORDER BY Album.Title, Track.Name

-- Q15. Every Jazz track: track name, album title and media type name, sorted by album then track.
SELECT Track.Name, Album.Title, MediaType.Name 
FROM Track
INNER JOIN Album ON Album.AlbumId = Track.AlbumId
INNER JOIN MediaType ON Track.MediaTypeId = MediaType.MediaTypeId
ORDER BY Album.Title, Track.Name;

-- Q16. Each customer with the employee who supports them: customer full name and rep full
--      name (one column each), sorted by rep then customer.
SELECT CONCAT(Customer.FirstName, " ", Customer.LastName) as customer_full_name, 
        CONCAT(Employee.FirstName, " ", Employee.LastName) as rep_full_name
FROM Customer
INNER JOIN Employee ON Customer.SupportRepId = Employee.EmployeeId
ORDER BY rep_full_name, customer_full_name;

-- Q17. Every employee and how many customers they support, including the employees who
--      support nobody (they show 0), most customers first, then last name.
SELECT CONCAT(e.FirstName, " ", e.LastName) as employee_name, COUNT(c.SupportRepId) as customer_support_count
FROM Employee as e
LEFT JOIN Customer as c
ON c.SupportRepId = e.EmployeeId
GROUP BY e.EmployeeId
ORDER BY customer_support_count DESC, e.LastName; 

-- Q18. The five genres that earned the most: genre name and revenue (the sum of unit price
--      times quantity over every invoice line, two decimals), highest first.
SELECT g.Name AS genre, ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue
FROM InvoiceLine AS il
JOIN Track AS t ON t.TrackId = il.TrackId
JOIN Genre AS g ON g.GenreId = t.GenreId
GROUP BY g.GenreId, g.Name
ORDER BY revenue DESC
LIMIT 5;

-- Q19. How many tracks have never been sold? One number, found with a LEFT JOIN
--      from Track to InvoiceLine and a test for NULL.
SELECT SUM(il.TrackId IS NULL)
FROM Track as t
LEFT JOIN InvoiceLine as il 
ON t.TrackId = il.TrackId;

-- ============================================================
-- Part D: subqueries
-- ============================================================

-- Q20. Every track on the album called Let There Be Rock: name and length in milliseconds,
--      in track order (by TrackId). Use a subquery for the album id, not a join.
SELECT Name, Milliseconds
FROM Track
WHERE AlbumId = (
    SELECT AlbumId
    FROM Album
    WHERE Title = 'Let There Be Rock'
)
ORDER BY TrackId;

-- Q21. Tracks that cost more than the average track price: name and unit price,
--      the first ten alphabetically.
SELECT Name, UnitPrice
FROM Track
WHERE UnitPrice > (
        SELECT AVG(UnitPrice)
        FROM Track
)
ORDER BY Name
LIMIT 10;

-- Q22. Artists with no album at all, A to Z. Write it with NOT IN and a subquery.
SELECT Name
FROM Artist
WHERE ArtistId NOT IN (
        SELECT ArtistId 
        FROM Album
)
ORDER BY Name;

-- Q22b. Same question, written as a LEFT JOIN. Same rows?
SELECT Name
FROM Artist as ar
LEFT JOIN Album as al 
ON ar.ArtistId = al.ArtistId
WHERE al.ArtistId IS NULL
ORDER BY ar.Name; 

-- Q23. The invoice with the highest total: invoice id, customer id, date and total.
SELECT InvoiceId, CustomerId, InvoiceDate, Total
FROM Invoice
WHERE Total = (
        SELECT MAX(Total) 
        FROM Invoice
);

SELECT InvoiceId, CustomerId, InvoiceDate, Total
FROM Invoice
ORDER BY Total DESC
LIMIT 1;

-- Q24. Customers who bought at least one Metal track: full name and country, sorted by
--      name. The list of customer ids comes from a subquery that joins Invoice,
--      InvoiceLine, Track and Genre.
SELECT CONCAT(FirstName, " ", LastName) as full_name, Country
FROM Customer
WHERE CustomerId IN (
        SELECT i.CustomerId
        FROM Invoice AS i
        JOIN InvoiceLine AS il ON il.InvoiceId = i.InvoiceId
        JOIN Track AS t ON t.TrackId = il.TrackId
        JOIN Genre AS g ON g.GenreId = t.GenreId
        WHERE g.Name = 'Metal'
)
ORDER BY full_name;

-- ============================================================
-- Stretch (for home, or if you finish early)
-- ============================================================

-- Q25. Each employee with the name of the person they report to. The general manager
--      reports to nobody and must still appear, with NULL. Hint: join Employee to
--      itself under two aliases.


-- Q26. Customers whose total spend is above the average customer's total spend: full name
--      and what they spent (two decimals), biggest first. The average of the per-customer
--      totals needs a subquery in FROM (the notes page calls it a derived table).

