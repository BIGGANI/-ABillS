<table>
<tr><th align=right bgcolor=$_COLORS[0]>PrivatBank</th></tr>
<tr><td>
<table>
<tr><td>$_ORDER:</td><td>%OPERATION_ID%</td></tr>
<tr><td>$_SUM:</td><td>%AMOUNT%</td></tr>
</table>


<FORM id='checkout' name='checkout' method=post action='https://www.verification.privatbank.ua/SENTRY/PaymentGateway/Application/CheckOutPage/CheckoutPage.aspx';>
<input id='Version' type='hidden' name='Version' value='1.0.0'>
	<input id='MerID' type='hidden' value='$conf{PAYSYS_PB_MERID}' name='MerID'>
	<input id='AcqID' type='hidden' value='414963' name='AcqID'>
	<input id='MerRespURL' type='hidden' value='https://www.verification.privatbank.ua/SENTRY/PaymentGateway/Application/wfrmresponse.aspx'  name='MerRespURL'>
	<input id='PurchaseAmt' type='hidden' value='%AMOUNT%' name='PurchaseAmt'>
	<input id='PurchaseCurrency' type='hidden' value='980' name='PurchaseCurrency'>
	<input id='PurchaseAmt2 type='hidden' value='%AMOUNT%' name='PurchaseAmt2'>
	<input id='PurchaseCurrency2' type='hidden' value='840' name='PurchaseCurrency2'>
	<input id='PurchaseCurrencyExponent' type='hidden' value='2' name='PurchaseCurrencyExponent'>
	<input id='OrderID' type='hidden' value='%OPERATION_ID%' name='OrderID'>
	<input id='SignatureMethod' type='hidden' value='SHA1' name='SignatureMethod'>
	<input id='Signature' type='hidden' value ='%HASH%' name='Signature'>
	<input id='CaptureFlag' type='hidden' value='A' name='CaptureFlag'>

<script>
document.getElementById('checkout').submit();
</script>
</FORM>


</td></tr>
</table>



