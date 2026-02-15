package ejerc01;

	/*
	 * Creamos la clase fecha sin main
	 * 
	 * declaramos el tipo enumerado para los meses
	 * 
	 * atributo para el dia mes (enumerado) y para el año
	 * 
	 * constructor que inicialice el mes al valor recibido por parametroy los demas a 0
	 * 
	 * otro constructor que inicialice todos los atributos de la clase.
	 * 
	 * Metodos para acceder y modificar cada uno de los atributos con get y set.
	 * 
	 * Metodo para ver si es verano
	 */

public class Fecha {
	
	//Atributos de fecha
	public enum enumMes{
		Enero,Febrero,Marzo,Abril,Mayo,Junio,Julio,Agosto,Septiembre,Octubre,Noviembre,Diciembre
	};
	private int dia;
	private enumMes mes;
	private int anio;

	//Constructores
	
	//inicializa el mes al valor recibido, demas a 0
	Fecha (enumMes mes){
		this.mes=mes;
		this.dia=0;
		this.anio=0;
	}
	
	//recibe todos los parametros
	Fecha (int dia, enumMes mes, int anio){
		this.mes=mes;
		this.dia=dia;
		this.anio=anio;		
	}
	
	//Metodos
	
	//Establecemos dia
	public int getDia() {
		return dia;
	}
	
	public void setDia(int dia) {
		this.dia=dia;
	}
	
	//Establecemos el mes
	public enumMes getMes() {
		return mes;
	}
	
	public void setMes(enumMes mes) {
		this.mes=mes;
	 * Metodo para ver si es verano
	 */

public class Fecha {
	
	//Atributos de fecha
	public enum enumMes{
		Enero,Febrero,Marzo,Abril,M
	}package ejerc01;

	/*
	 * Creamos la clase fecha sin main
	 * 
	 * declaramos el tipo enumerado para los meses
	 * 
	 * atributo para el dia mes (enumerado) y para el año
	 * 
	 * constructor que inicialice el mes al valor recibido por parametroy los demas a 0
	 * 
	 * otro constructor que inicialice todos los atributos de la clase.
	 * 
	 * Metodos para acceder y modificar cada uno de los atributos con get y set.
	 * 
	 * Metodo para ver si es verano
	 */

public class Fecha {
	
	//Atributos de fecha
	public enum enumMes{
		Enero,Febrero,Marzo,Abril,Mayo,Junio,Julio,Agosto,Septiembre,Octubre,Noviembre,Diciembre
	};
	private int dia;
	private enumMes mes;
	private int anio;

	//Constructores
	
	//inicializa el mes al valor recibido, demas a 0
	Fecha (enumMes mes){
		this.mes=mes;
		this.dia=0;
		this.anio=0;
	}
	
	//recibe todos los parametros
	Fecha (int dia, enumMes mes, int anio){
		this.mes=mes;
		this.dia=dia;
		this.anio=anio;		
	}
	
	//Metodos
	
	//Establecemos dia
	public int getDia() {
		return dia;
	}
	
	public void setDia(int dia) {
		this.dia=dia;
	}
	
	//Establecemos el mes
	public enumMes getMes() {
		return mes;
	}
	
	public void setMes(enumMes mes) {
		this.mes=mes;
	}
	
	//Establecemos el año
	public int getAnio() {
		return anio;
	}
	
	public void setAnio(int anio) {
		this.anio=anio;
	}
	
	//Saber si es verano o no
	public boolean isSummer() {
		if(mes==enumMes.Junio || mes==enumMes.Julio || mes==enumMes.Agosto) {
			return true;
		}
		else{
			return false;
		}
	}//Fin de metodo verano
	
	//Imprimimos el formato de fecha
	public String toString() {
		return this.dia + " de " + this.mes + " de " + this.anio;
	}
		
}	//Final de la clase fecha
	
	//Establecemos el año
	public int getAnio() {
		return anio;
	}
	
	public void setAnio(int anio) {
		this.anio=anio;
	}
	
	//Saber si es verano o no
	public boolean isSummer() {
		if(mes==enumMes.Junio || mes==enumMes.Julio || mes==enumMes.Agosto) {
			return true;
		}
		else{
			return false;
		}
	}//Fin de metodo verano
	
	//Imprimimos el formato de fecha
	public String toString() {
		return this.dia + " de " + this.mes + " de " + this.anio;
	}
		
}	//Final de la clase fecha