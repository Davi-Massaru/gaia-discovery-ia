Class Gaia.Data.DiscoveryReport Extends %Persistent
{
Property RunId As %String(MAXLEN = 64);
Property DiaObjectId As %String(MAXLEN = 100);
Property DiaSourceId As %String(MAXLEN = 100);
Property Tag As %String(MAXLEN = 100);
Property CreatedAt As %String(MAXLEN = 40);
Property InteropSessionId As %String(MAXLEN = 100);
Property Summary As %String(MAXLEN = 4000);
Property EvidenceJSON As %String(MAXLEN = 1000000);
Property SearchText As %String(MAXLEN = 12000);
Property EmbeddingModel As %String(MAXLEN = 100);
Property RA As %Double;
Property Dec As %Double;
Property ObservedMjdTai As %Double;
Property SciencePNG As %Stream.GlobalBinary;
Property TemplatePNG As %Stream.GlobalBinary;
Property DifferencePNG As %Stream.GlobalBinary;
Property Assessment As %String(VALUELIST = ",CATALOG_CONTEXT_FOUND,REVIEW_CANDIDATE,INCONCLUSIVE");
Property ReviewStatus As %String(VALUELIST = ",NOT_REQUIRED,PENDING,ACCEPTED_FOR_REVIEW,REJECTED,TASK_ERROR");
Property SearchEmbedding As %Vector(DATATYPE = "FLOAT", LEN = 1536);
Index RunIndex On RunId;
Index ObjectIndex On DiaObjectId;
}
