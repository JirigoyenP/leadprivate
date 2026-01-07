
DO $$
DECLARE 
	array_keywords_text TEXT[];
	keywords_used_array TEXT[]:=array['1','2','3'];
BEGIN
	SELECT ARRAY_AGG(keyword_text)FROM keywords WHERE is_deleted=FALSE INTO array_keywords_text;	
	/*Select * from keyword_text;*/
	/*raise notice 'Array %',array_keywords_text;*/
	/*SELECT keyword_text into array_keywords_text FROM keywords WHERE is_deleted=FALSE;*/

END;
$$;