package com.gaia.discovery.pex;

import com.intersystems.enslib.pex.OutboundAdapter;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import java.net.URI;
import java.net.URLEncoder;
import javax.net.ssl.HttpsURLConnection;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.ArrayList;
import java.util.List;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.net.ConnectException;
import javax.net.ssl.SSLException;

/** Shared transport only: scientific queries and CSV interpretation belong to IRIS Python. */
public final class TapOutboundAdapter extends OutboundAdapter {
    private static final Map<String,String> ENDPOINTS = Map.of(
        "GAIA", "https://gea.esac.esa.int/tap-server/tap/sync",
        "SIMBAD", "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
        "IRSA", "https://irsa.ipac.caltech.edu/TAP/sync");
    private static final int MAX_BYTES = 1024 * 1024;
    private static final String SIMBAD_MIRROR = "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync";
    private final ObjectMapper json = new ObjectMapper();
    @Override public void OnInit() { }
    @Override public void OnTearDown() { }

    public String query(String catalog, String adql, int maxRows, int timeoutSeconds) throws Exception {
        long started = System.nanoTime();
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("catalog", catalog); result.put("status", "ERROR"); result.put("httpStatus", 0);
        String endpoint = ENDPOINTS.get(catalog);
        if (endpoint == null || maxRows < 1 || maxRows > 20 || timeoutSeconds < 1 || timeoutSeconds > 45
                || adql == null || adql.length() > 4096 || !adql.matches("(?is)^SELECT TOP (?:[1-9]|1[0-9]|20) .+")
                || adql.contains(";") || adql.contains("--")) {
            result.put("errorCode", "INVALID_TAP_REQUEST");
        } else {
            String body = "REQUEST=doQuery&LANG=ADQL&FORMAT=csv&MAXREC="+maxRows+"&QUERY="+URLEncoder.encode(adql, StandardCharsets.UTF_8);
            long deadline = started + timeoutSeconds * 1000000000L;
            List<Map<String,Object>> attempts = new ArrayList<>();
            for (int attempt=0; attempt<2 && System.nanoTime()<deadline; attempt++) {
              String target = catalog.equals("SIMBAD") && attempt==1 ? SIMBAD_MIRROR : endpoint;
              long attemptStarted = System.nanoTime();
              long attemptDeadline = catalog.equals("SIMBAD") && attempt==0
                  ? Math.min(deadline, attemptStarted+10000000000L) : deadline;
              Map<String,Object> trace = new LinkedHashMap<>();
              trace.put("endpoint", target); trace.put("httpStatus", 0);
              result.put("endpoint", target); result.put("httpStatus", 0);
              String phase = "CONNECT";
              HttpsURLConnection connection = null;
              try {
                // Both TAP services accept GET. Gaia's small, bounded query is
                // sent as GET; other catalogs retain form-encoded POST.
                boolean useGet = catalog.equals("GAIA") && body.length()<=6000;
                trace.put("method", useGet ? "GET" : "POST");
                connection = (HttpsURLConnection) URI.create(target+(useGet ? "?"+body : "")).toURL().openConnection();
                connection.setConnectTimeout(Math.min(5000,remainingMillis(attemptDeadline)));
                connection.setReadTimeout(remainingMillis(attemptDeadline));
                connection.setInstanceFollowRedirects(false);
                connection.setRequestMethod(useGet ? "GET" : "POST");
                connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                connection.setRequestProperty("Accept", "text/csv");
                connection.setRequestProperty("User-Agent", "GaiaDiscoveryAI/1.0");
                if (!useGet) {
                    connection.setDoOutput(true);
                    connection.setFixedLengthStreamingMode(body.getBytes(StandardCharsets.UTF_8).length);
                }
                phase = "CONNECT_TLS";
                connection.connect();
                phase = "REQUEST";
                connection.setReadTimeout(remainingMillis(attemptDeadline));
                if (!useGet) {
                    try (var output = connection.getOutputStream()) { output.write(body.getBytes(StandardCharsets.UTF_8)); }
                }
                phase = "RESPONSE";
                int status = connection.getResponseCode();
                result.put("httpStatus", status);
                trace.put("httpStatus", status);
                if (status != 200) throw new java.io.IOException("Non-200 TAP response");
                phase = "READ";
                try (InputStream input = connection.getInputStream(); ByteArrayOutputStream buffer = new ByteArrayOutputStream()) {
                    byte[] chunk = new byte[8192];
                    int length;
                    while (true) {
                        connection.setReadTimeout(remainingMillis(attemptDeadline));
                        length = input.read(chunk);
                        if (length == -1) break;
                        buffer.write(chunk,0,length);
                        if (buffer.size()>MAX_BYTES) break;
                    }
                    byte[] bytes = buffer.toByteArray();
                    if (bytes.length > MAX_BYTES) { result.put("errorCode", "TAP_RESPONSE_TOO_LARGE"); trace.put("errorCode", "TAP_RESPONSE_TOO_LARGE"); }
                    else { result.put("status", "OK"); result.put("csvBody", new String(bytes, StandardCharsets.UTF_8)); result.remove("errorCode"); result.remove("errorType"); result.remove("failurePhase"); }
                }
            } catch (Exception error) {
                int status = (int) result.get("httpStatus");
                String code = status != 0 && status != 200 ? "TAP_HTTP_ERROR" :
                    error instanceof SocketTimeoutException ? "TAP_TIMEOUT" :
                    error instanceof UnknownHostException ? "TAP_DNS_ERROR" :
                    error instanceof SSLException ? "TAP_TLS_ERROR" :
                    error instanceof ConnectException ? "TAP_CONNECTION_ERROR" : "TAP_TRANSPORT_ERROR";
                result.put("errorCode", code);
                result.put("errorType", error.getClass().getSimpleName());
                result.put("failurePhase", phase);
                trace.put("errorCode", code); trace.put("errorType", error.getClass().getSimpleName()); trace.put("failurePhase", phase);
            }
            finally {
                if (connection != null) connection.disconnect();
                trace.put("elapsedMs", (System.nanoTime()-attemptStarted)/1000000);
                attempts.add(trace);
            }
            int status = (int) result.get("httpStatus");
            if (result.get("status").equals("OK") || result.get("errorCode").equals("TAP_RESPONSE_TOO_LARGE")
                || status>=400 && status<500 && status!=408) break;
          }
          result.put("attempts", attempts);
        }
        result.put("elapsedMs", (System.nanoTime()-started)/1000000);
        return json.writeValueAsString(result);
    }

    private static int remainingMillis(long deadline) throws SocketTimeoutException {
        long remaining = (deadline-System.nanoTime())/1000000;
        if (remaining<=0) throw new SocketTimeoutException("TAP deadline");
        return (int)Math.min(remaining,Integer.MAX_VALUE);
    }
}
