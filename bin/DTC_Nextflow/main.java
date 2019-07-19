package DTC_Nextflow;
import fr.limsi.dctfinder.DCTExtractor;
import fr.limsi.dctfinder.DCTExtractorException;
import fr.limsi.dctfinder.PageInfo;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.io.*;

public class main {


    public static void main(String[] args) {
        Calendar dctCalendar=null;
        String inputString=" ";
        try {
            Path wapitiBinaryFile = Paths.get("/usr/local/bin/wapiti");
            DCTExtractor extractor = new DCTExtractor(wapitiBinaryFile);
            inputString=String.join(" ", args);
            if (args.length<1) throw  new RuntimeException("Enter a valid parameter");
            Locale locale = Locale.ENGLISH;

            //InputStream is = new FileInputStream(new File(path));
            InputStream is = new ByteArrayInputStream(inputString.getBytes(StandardCharsets.UTF_8));

            Calendar downloadDate = new GregorianCalendar();

            PageInfo pageInfo = extractor.getPageInfos(is, null, locale, downloadDate);
            dctCalendar = pageInfo.getDCT();
            Date calendarDate = dctCalendar.getTime();
            System.out.println(calendarDate);


        }catch (DCTExtractorException e ){
            System.out.println(e.getMessage()+"DCTExtractorException ");
        }catch(NullPointerException e){
            System.out.println(dctCalendar);
        }

        }


}
