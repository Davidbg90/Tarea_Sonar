package ejerc01;

import ejerc01.Fecha.enumMes;

/*
 * Objeto de la clase fecha
 * 
 * actualizamos datos
 * 
 * muestra fecha formato largo
 * 
 * mostramos si es verano
 * 
 * otro obejeto de la clase fecha
 * 
 * muestra el año
 * 
 * fecha en formato largo
 * 
 * muestra si es verano o no
 */

public class Principal {

	public static void main(String[] args) {
		
		//Creamos los objetos
		Fecha objFecha1 = new Fecha (enumMes.Julio);
		Fecha objFecha2 = new Fecha (13, enumMes.Febrero, 2025);
		
		//Establecemos un dia y un año mediante metodo set
		objFecha1.setDia(21);
		objFecha1.setAnio(1990);
		
		//Ejecutamos las dos fechas
		System.out.println("========Primera fecha========");
		System.out.println(objFecha1.toString());									//Mostramos la fecha en formato largo
		System.out.println(objFecha1.isSummer() ? "Es verano" : "No es verano");	//Mostramos si es verano o no
	
		System.out.println("========Segunda fecha========");
		System.out.println("La fecha 2 contiene el año " + objFecha2.getAnio());
		System.out.println(objFecha2.toString());									//Mostramos la fecha en formato largo
		System.out.println(objFecha2.isSummer() ? "Es verano" : "No es verano");	//Mostramos si es verano o no

	}	//Fin de main

}	//Fin de programa