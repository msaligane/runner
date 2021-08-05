using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Text.Json;


namespace GitHub.Runner.Sdk
{

    public static class VersionProvider
    {
        private static readonly HttpClient client = new HttpClient();
        private static string uri = @"http://localhost:15789";

        public static string getVersion()
        {
            string result = requestVersion().Result;
            // deserialize the response which has the same structure as VersionResponse class
            VersionResponse response = JsonSerializer.Deserialize<VersionResponse>(result);
            Console.WriteLine("Version Provider returned version: {0}", response.version);
            return response.version;
        }

        private async static Task<string> requestVersion()
        {
            try
            {
                string responseBody = await client.GetStringAsync(uri);
                return responseBody;
            }
            catch(HttpRequestException e)
            {
                Console.WriteLine("\nCaught an exception when requesting the Runner Version:");
                Console.WriteLine("Message :{0} ",e.Message);
                return "";
            }
        }

        private class VersionResponse {
            public string version {get; set;}
            public string timestamp {get; set;}
        }
    }
}

